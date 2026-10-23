#!/usr/bin/env python3
"""
ChronosAR: Intelligent WebAR Spatial Museum Guide Server
Final Year CSE PBL (AR/VR Specialization)

Standalone Python 3 HTTP & REST API Server (Zero pip dependencies).
Uses standard library: http.server, socket, json, os, urllib.
"""

import http.server
import socketserver
import json
import os
import socket
import sys
import urllib.parse
from datetime import datetime

# Ensure utf-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PORT = int(os.environ.get("PORT", 3000))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
DATA_DIR = os.path.join(BASE_DIR, "data")
EXHIBITS_FILE = os.path.join(DATA_DIR, "exhibits.json")
ANALYTICS_FILE = os.path.join(DATA_DIR, "analytics.json")

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".patt": "text/plain",
    ".wasm": "application/wasm",
    ".gltf": "model/gltf+json",
    ".glb": "model/gltf-binary"
}

def read_json(file_path, default=None):
    if default is None:
        default = {}
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return default

def write_json(file_path, data):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error writing {file_path}: {e}")
        return False

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

class MuseumRequestHandler(http.server.BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/exhibits":
            data = read_json(EXHIBITS_FILE, [])
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        if path.startswith("/api/exhibits/"):
            ex_id = path.replace("/api/exhibits/", "")
            exhibits = read_json(EXHIBITS_FILE, [])
            match = next((e for e in exhibits if e.get("id") == ex_id), None)
            if match:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(match).encode("utf-8"))
            else:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Exhibit not found"}).encode("utf-8"))
            return

        if path == "/api/analytics":
            data = read_json(ANALYTICS_FILE, {})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        # Static File Serving
        req_path = path.lstrip("/")
        if not req_path:
            req_path = "index.html"
        
        file_path = os.path.normpath(os.path.join(PUBLIC_DIR, req_path))

        if not file_path.startswith(PUBLIC_DIR) or not os.path.isfile(file_path):
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"404 Not Found: {path}".encode("utf-8"))
            return

        ext = os.path.splitext(file_path)[1].lower()
        content_type = MIME_TYPES.get(ext, "application/octet-stream")

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"

        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if path == "/api/analytics/event":
            analytics = read_json(ANALYTICS_FILE, {
                "total_visitors": 0, "total_scans": 0, "recent_events": []
            })
            if payload.get("type") == "marker_scan":
                analytics["total_scans"] = analytics.get("total_scans", 0) + 1
            if payload.get("type") == "session_start":
                analytics["total_visitors"] = analytics.get("total_visitors", 0) + 1

            analytics.setdefault("recent_events", []).insert(0, {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                **payload
            })
            analytics["recent_events"] = analytics["recent_events"][:50]
            write_json(ANALYTICS_FILE, analytics)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
            return

        if path == "/api/quiz/submit":
            analytics = read_json(ANALYTICS_FILE, {})
            analytics.setdefault("recent_events", []).insert(0, {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "type": "quiz_submitted",
                "score": f"{payload.get('score', 0)}/{payload.get('total', 5)}",
                "student_name": payload.get("name", "Student Explorer"),
                "certificate_id": payload.get("certificate_id", "CERT-DEMO")
            })
            write_json(ANALYTICS_FILE, analytics)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

if __name__ == "__main__":
    local_ip = get_local_ip()
    print("=" * 65)
    print("[CHRONOS-AR] PYTHON WEBAR BACKEND SERVER")
    print("Final Year CSE Project-Based Learning (AR/VR Specialization)")
    print("=" * 65)
    print(f"\n>> Running on port {PORT}:")
    print(f"   -> Localhost:       http://localhost:{PORT}")
    print(f"   -> Network (Phone): http://{local_ip}:{PORT}")
    print("\n>> Endpoints:")
    print(f"   * AR Guide & 3D Hall:   http://localhost:{PORT}/index.html")
    print(f"   * AR Marker Studio:     http://localhost:{PORT}/markers.html")
    print(f"   * Curator Dashboard:    http://localhost:{PORT}/curator.html")
    print(f"   * Viva & Architecture:  http://localhost:{PORT}/docs.html")
    print("=" * 65)

    with socketserver.TCPServer(("0.0.0.0", PORT), MuseumRequestHandler) as httpd:
        httpd.serve_forever()
