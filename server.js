/**
 * ChronosAR: Intelligent WebAR Spatial Museum Guide Server
 * Final Year CSE PBL (AR/VR Specialization)
 * 
 * Standalone Zero-Dependency Node.js HTTP & REST API Server.
 * Supports Local Network Access (Wi-Fi QR scan) for mobile WebAR testing.
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');

const PORT = process.env.PORT || 3000;
const PUBLIC_DIR = path.join(__dirname, 'public');
const DATA_DIR = path.join(__dirname, 'data');
const EXHIBITS_FILE = path.join(DATA_DIR, 'exhibits.json');
const ANALYTICS_FILE = path.join(DATA_DIR, 'analytics.json');

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.mjs': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.wav': 'audio/wav',
  '.mp3': 'audio/mpeg',
  '.patt': 'text/plain',
  '.wasm': 'application/wasm',
  '.gltf': 'model/gltf+json',
  '.glb': 'model/gltf-binary'
};

// Helpers for Data I/O
function readJSON(file, fallback = {}) {
  try {
    if (fs.existsSync(file)) {
      return JSON.parse(fs.readFileSync(file, 'utf8'));
    }
  } catch (err) {
    console.error(`Error reading ${file}:`, err.message);
  }
  return fallback;
}

function writeJSON(file, data) {
  try {
    fs.writeFileSync(file, JSON.stringify(data, null, 2), 'utf8');
    return true;
  } catch (err) {
    console.error(`Error writing ${file}:`, err.message);
    return false;
  }
}

// Get local IPv4 addresses for mobile testing
function getLocalIPs() {
  const interfaces = os.networkInterfaces();
  const addresses = [];
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      if (iface.family === 'IPv4' && !iface.internal) {
        addresses.push(iface.address);
      }
    }
  }
  return addresses;
}

// Request dispatcher
const server = http.createServer((req, res) => {
  // CORS & Security Headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  const parsedUrl = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const pathname = parsedUrl.pathname;

  // --- REST API ROUTES ---
  if (pathname === '/api/exhibits' && req.method === 'GET') {
    const exhibits = readJSON(EXHIBITS_FILE, []);
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(exhibits));
    return;
  }

  if (pathname.startsWith('/api/exhibits/') && req.method === 'GET') {
    const id = pathname.replace('/api/exhibits/', '');
    const exhibits = readJSON(EXHIBITS_FILE, []);
    const found = exhibits.find(e => e.id === id);
    if (found) {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(found));
    } else {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Exhibit not found' }));
    }
    return;
  }

  if (pathname === '/api/exhibits' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const newExhibit = JSON.parse(body);
        const exhibits = readJSON(EXHIBITS_FILE, []);
        const idx = exhibits.findIndex(e => e.id === newExhibit.id);
        if (idx >= 0) {
          exhibits[idx] = { ...exhibits[idx], ...newExhibit };
        } else {
          newExhibit.id = newExhibit.id || `exhibit_${Date.now()}`;
          exhibits.push(newExhibit);
        }
        writeJSON(EXHIBITS_FILE, exhibits);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, exhibit: newExhibit }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON payload' }));
      }
    });
    return;
  }

  if (pathname === '/api/analytics' && req.method === 'GET') {
    const analytics = readJSON(ANALYTICS_FILE, {});
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(analytics));
    return;
  }

  if (pathname === '/api/analytics/event' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const eventData = JSON.parse(body);
        const analytics = readJSON(ANALYTICS_FILE, {
          total_visitors: 0,
          total_scans: 0,
          popular_exhibits: [],
          recent_events: []
        });

        if (eventData.type === 'marker_scan') {
          analytics.total_scans = (analytics.total_scans || 0) + 1;
        }
        if (eventData.type === 'session_start') {
          analytics.total_visitors = (analytics.total_visitors || 0) + 1;
        }

        analytics.recent_events = analytics.recent_events || [];
        analytics.recent_events.unshift({
          timestamp: new Date().toISOString(),
          ...eventData
        });
        if (analytics.recent_events.length > 50) {
          analytics.recent_events.pop();
        }

        writeJSON(ANALYTICS_FILE, analytics);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid event payload' }));
      }
    });
    return;
  }

  if (pathname === '/api/quiz/submit' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const quizData = JSON.parse(body);
        const analytics = readJSON(ANALYTICS_FILE, {});
        analytics.recent_events = analytics.recent_events || [];
        analytics.recent_events.unshift({
          timestamp: new Date().toISOString(),
          type: 'quiz_submitted',
          score: `${quizData.score}/${quizData.total}`,
          student_name: quizData.name || 'Anonymous Explorer',
          certificate_id: quizData.certificate_id || `CERT-${Date.now().toString(36).toUpperCase()}`
        });
        writeJSON(ANALYTICS_FILE, analytics);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, certificate_id: quizData.certificate_id }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Quiz submission error' }));
      }
    });
    return;
  }

  // --- STATIC FILE SERVING ---
  let safePath = path.normalize(pathname).replace(/^(\.\.[\/\\])+/, '');
  if (safePath === '/' || safePath === '\\') safePath = '/index.html';

  const filePath = path.join(PUBLIC_DIR, safePath);

  // Security check against directory traversal
  if (!filePath.startsWith(PUBLIC_DIR)) {
    res.writeHead(403, { 'Content-Type': 'text/plain' });
    res.end('403 Forbidden');
    return;
  }

  fs.stat(filePath, (err, stats) => {
    if (err || !stats.isFile()) {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end(`404 Not Found: ${safePath}`);
      return;
    }

    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';

    res.writeHead(200, { 'Content-Type': contentType });
    const readStream = fs.createReadStream(filePath);
    readStream.pipe(res);
  });
});

server.listen(PORT, '0.0.0.0', () => {
  const localIPs = getLocalIPs();
  console.log('='.repeat(65));
  console.log('🏛️  CHRONOS-AR: INTELLIGENT WEBAR SPATIAL MUSEUM GUIDE');
  console.log('🎓 Final Year CSE Project-Based Learning (AR/VR Specialization)');
  console.log('='.repeat(65));
  console.log(`\n🚀 Server listening on port ${PORT}:`);
  console.log(`   ➜ Localhost:      http://localhost:${PORT}`);
  localIPs.forEach(ip => {
    console.log(`   ➜ Network (Phone): http://${ip}:${PORT}`);
  });
  console.log('\n📖 Available Pages:');
  console.log(`   • AR Guide & 3D Hall:   http://localhost:${PORT}/index.html`);
  console.log(`   • AR Marker Studio:     http://localhost:${PORT}/markers.html`);
  console.log(`   • Curator Dashboard:    http://localhost:${PORT}/curator.html`);
  console.log(`   • Viva & Architecture:  http://localhost:${PORT}/docs.html`);
  console.log('='.repeat(65));
});
