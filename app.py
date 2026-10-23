"""
AetherPlan AAI: Autonomous Multi-Agent Adaptive Study Planner
Final Year CSE Engineering Project-Based Learning (PBL) System
Author: CSE Engineering PBL Team
"""

import streamlit as st
import pandas as pd
import numpy as np
import datetime
import math
import time
from typing import Dict, Any, List

from core.models import StudentProfile, Chronotype, BloomTaxonomy, SessionType
from core.database import DatabaseManager
from core.sm2 import SM2Calculator, calculate_retention_probability
from agents.orchestrator import StudyPlannerOrchestrator


# --- Page Configuration ---
st.set_page_config(
    page_title="AetherPlan AAI | Autonomous Study Planner",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling (Dark Glassmorphism & High-Contrast Visuals) ---
st.markdown("""
<style>
    /* Modern typography and theme styling */
    .main-header {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.3rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        text-align: center;
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #38bdf8;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 4px;
    }
    .badge-learning { background-color: #1e3a8a; color: #93c5fd; }
    .badge-review { background-color: #064e3b; color: #6ee7b7; }
    .badge-bloom-rem { background-color: #374151; color: #d1d5db; }
    .badge-bloom-und { background-color: #1e293b; color: #38bdf8; }
    .badge-bloom-app { background-color: #064e3b; color: #34d399; }
    .badge-bloom-ana { background-color: #78350f; color: #fcd34d; }
    .badge-bloom-eva { background-color: #831843; color: #f472b6; }
    .badge-bloom-cre { background-color: #581c87; color: #c084fc; }
    .session-card {
        background: rgba(30, 41, 59, 0.6);
        border-left: 4px solid #6366f1;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
    }
    .session-card-completed {
        background: rgba(15, 23, 42, 0.5);
        border-left: 4px solid #10b981;
        opacity: 0.8;
    }
    .flashcard-box {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border: 2px solid #3b82f6;
        border-radius: 16px;
        padding: 24px;
        min-height: 180px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        font-size: 1.25rem;
        font-weight: 500;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        margin-bottom: 15px;
    }
    .thought-trace {
        font-family: 'Courier New', Courier, monospace;
        background: #090d16;
        border-left: 3px solid #8b5cf6;
        padding: 10px;
        border-radius: 4px;
        font-size: 0.85rem;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)


# --- Initialize State ---
if "db" not in st.session_state:
    st.session_state.db = DatabaseManager()

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = StudyPlannerOrchestrator(db_manager=st.session_state.db)

if "active_plan" not in st.session_state:
    st.session_state.active_plan = st.session_state.db.get_latest_active_plan()

if "quiz_active_topic" not in st.session_state:
    st.session_state.quiz_active_topic = None

if "current_quiz_questions" not in st.session_state:
    st.session_state.current_quiz_questions = None

if "flashcard_index" not in st.session_state:
    st.session_state.flashcard_index = 0

if "show_flashcard_answer" not in st.session_state:
    st.session_state.show_flashcard_answer = False


# --- Helper Function: Seed CSE Demo Curriculum ---
def seed_demo_cse_curriculum():
    profile = StudentProfile(
        name="Alex Mercer (Final Year CSE)",
        semester="Semester 8",
        branch="Computer Science & Engineering",
        daily_available_hours=4.5,
        chronotype=Chronotype.BALANCED,
        preferred_session_minutes=60,
        break_duration_minutes=15,
        fatigue_threshold_hours=5.0
    )

    subjects_input = [
        {
            "name": "Operating Systems",
            "priority": 5,
            "exam_date": (datetime.date.today() + datetime.timedelta(days=21)).strftime("%Y-%m-%d"),
            "syllabus": """
            - Process Management, Context Switching & State Transitions
            - CPU Scheduling Algorithms: FCFS, Shortest Job First (SJF), Round Robin
            - Process Synchronization, Critical Section Problem, Mutex & Semaphores
            - Deadlock: Characterization, Prevention, Avoidance (Banker's Algorithm), Detection
            - Memory Management, Paging, Segmentation, Page Replacement (LRU, Optimal)
            - File System Implementation, Disk Scheduling (SCAN, C-SCAN)
            """
        },
        {
            "name": "Machine Learning",
            "priority": 4,
            "exam_date": (datetime.date.today() + datetime.timedelta(days=28)).strftime("%Y-%m-%d"),
            "syllabus": """
            - Supervised Learning Foundations, Cost Functions, Gradient Descent
            - Linear Regression and Logistic Regression with Regularization (L1/L2)
            - Decision Trees, Information Gain, Random Forests & Gradient Boosting
            - Support Vector Machines (SVM), Maximum Margin, Kernel Trick
            - Unsupervised Learning: K-Means Clustering, Principal Component Analysis (PCA)
            - Artificial Neural Networks, Activation Functions & Backpropagation Algorithm
            """
        },
        {
            "name": "Computer Networks",
            "priority": 3,
            "exam_date": (datetime.date.today() + datetime.timedelta(days=35)).strftime("%Y-%m-%d"),
            "syllabus": """
            - OSI vs TCP/IP Reference Architectures and Layer Functions
            - Data Link Layer Framing, Error Detection (CRC) and Flow Control
            - Network Layer: IPv4/IPv6 Addressing, Subnetting, Classless CIDR
            - Routing Protocols: Distance Vector vs Link State (Dijkstra)
            - Transport Layer: TCP 3-Way Handshake, Flow Control, Congestion Control
            - Application Layer Protocols: DNS Hierarchy, HTTP/1.1 vs HTTP/2
            """
        }
    ]

    with st.spinner("🤖 Multi-Agent Orchestrator decomposing syllabus, profiling cognitive load & solving CSP constraints..."):
        new_plan = st.session_state.orchestrator.create_complete_study_plan(
            title="Final Year CSE Engineering Comprehensive PBL Plan",
            subject_data=subjects_input,
            profile=profile,
            exam_target_date=(datetime.date.today() + datetime.timedelta(days=28)).strftime("%Y-%m-%d")
        )
        st.session_state.active_plan = new_plan
        st.success("✨ Autonomous Study Plan generated successfully with SM-2 Spaced Repetition & CSP Schedule!")
        st.rerun()


# --- Sidebar Navigation & Settings ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/brain.png", width=64)
    st.title("AetherPlan AAI")
    st.caption("Autonomous Agentic AI Study Planner\nFinal Year CSE Engineering PBL")

    st.markdown("---")
    st.subheader("👤 Student Profile")
    student_name = st.text_input("Student Name", value=st.session_state.active_plan.profile.name if st.session_state.active_plan else "Alex Mercer")
    daily_hrs = st.slider("Daily Study Budget (Hours)", 1.0, 8.0, value=float(st.session_state.active_plan.profile.daily_available_hours) if st.session_state.active_plan else 4.0, step=0.5)
    
    chronotype_options = [Chronotype.MORNING_LARK.value, Chronotype.BALANCED.value, Chronotype.NIGHT_OWL.value]
    default_chrono_idx = 1
    if st.session_state.active_plan:
        try:
            default_chrono_idx = chronotype_options.index(st.session_state.active_plan.profile.chronotype.value)
        except ValueError:
            default_chrono_idx = 1

    selected_chrono = st.selectbox("Circadian Chronotype", chronotype_options, index=default_chrono_idx)

    st.markdown("---")
    st.subheader("⚡ Agent Intelligence Mode")
    llm_provider = st.selectbox("Inference Engine", ["Built-in Academic Engine (Offline)", "Google Gemini API", "OpenAI GPT-4o-mini"])
    api_key_input = None
    if "Gemini" in llm_provider or "OpenAI" in llm_provider:
        api_key_input = st.text_input("Enter API Key (Optional)", type="password", help="If left empty, system operates in resilient Offline Heuristic Engine mode.")

    st.markdown("---")
    if st.button("🚀 Load Demo CSE Curriculum", use_container_width=True, type="primary"):
        seed_demo_cse_curriculum()

    if st.session_state.active_plan:
        if st.button("🔄 Auto-Heal & Reschedule", use_container_width=True):
            with st.spinner("Reflexion Agent analyzing backlog and rebalancing timetable..."):
                healed = st.session_state.orchestrator.trigger_adaptive_rescheduling(st.session_state.active_plan)
                st.session_state.active_plan = healed
                st.toast("Schedule healed and rebalanced!", icon="✅")
                st.rerun()


# --- Main Dashboard ---
st.markdown('<div class="main-header">AetherPlan AAI: Smart Study Planner Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Applied Autonomous Multi-Agent Architecture for Cognitive Timetabling & Spaced Repetition (CSE PBL)</div>', unsafe_allow_html=True)

# Top Metric Banner
if st.session_state.active_plan:
    plan = st.session_state.active_plan
    all_sess = plan.sessions
    completed_sess = [s for s in all_sess if s.completed]
    pct_complete = round((len(completed_sess) / max(1, len(all_sess))) * 100, 1)

    due_cards = st.session_state.db.get_due_flashcards()
    all_quizzes = st.session_state.db.get_all_quiz_results()
    avg_score = round(sum(q.percentage for q in all_quizzes) / max(1, len(all_quizzes)), 1) if all_quizzes else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""<div class="metric-card"><div class="metric-val">{len(all_sess)}</div><div class="metric-label">Total Sessions</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card"><div class="metric-val">{pct_complete}%</div><div class="metric-label">Completed</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card"><div class="metric-val">{len(due_cards)}</div><div class="metric-label">Due Reviews</div></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-card"><div class="metric-val">{avg_score}%</div><div class="metric-label">Avg Quiz Score</div></div>""", unsafe_allow_html=True)
    with c5:
        st.markdown(f"""<div class="metric-card"><div class="metric-val">{len(plan.subjects)}</div><div class="metric-label">Active Subjects</div></div>""", unsafe_allow_html=True)

    st.write("")
else:
    st.info("👋 Welcome to **AetherPlan AAI**! Click **'Load Demo CSE Curriculum'** in the sidebar to generate a complete multi-agent plan, or create one in the Curriculum tab.")


# --- Main Tabs Navigation ---
tab_schedule, tab_curriculum, tab_sm2, tab_quiz, tab_pomodoro, tab_analytics, tab_traces = st.tabs([
    "📅 Schedule & Sessions",
    "📚 Curriculum & Knowledge DAG",
    "🧠 Spaced Repetition (SM-2)",
    "🎯 Diagnostic Quiz",
    "⏱️ Focus Pomodoro",
    "📈 Cognitive Analytics",
    "🤖 Agent Thought Traces"
])


# ==========================================================
# TAB 1: SCHEDULE & SESSIONS
# ==========================================================
with tab_schedule:
    if not st.session_state.active_plan:
        st.warning("Please create or load a study plan from the sidebar to view your schedule.")
    else:
        plan = st.session_state.active_plan
        col_f1, col_f2, col_f3 = st.columns([2, 2, 2])
        with col_f1:
            subject_filter = st.selectbox("Filter Subject", ["All Subjects"] + [s.name for s in plan.subjects])
        with col_f2:
            status_filter = st.selectbox("Filter Status", ["All Sessions", "Pending Only", "Completed Only"])
        with col_f3:
            date_filter = st.date_input("Jump to Date", value=datetime.date.today() + datetime.timedelta(days=1))

        # Filter sessions
        filtered_sessions = plan.sessions
        if subject_filter != "All Subjects":
            filtered_sessions = [s for s in filtered_sessions if s.subject_name == subject_filter]
        if status_filter == "Pending Only":
            filtered_sessions = [s for s in filtered_sessions if not s.completed]
        elif status_filter == "Completed Only":
            filtered_sessions = [s for s in filtered_sessions if s.completed]

        st.markdown("### 🗓️ Chronotype-Aligned Timetable")
        st.caption(f"Circadian Peak Optimization: **{plan.profile.chronotype.value}** | Daily Study Cap: **{plan.profile.daily_available_hours} hours**")

        # Group sessions by date
        dates_in_view = sorted(list({s.scheduled_date for s in filtered_sessions}))
        if not dates_in_view:
            st.info("No sessions match the current filter.")

        for day_str in dates_in_view:
            day_sessions = [s for s in filtered_sessions if s.scheduled_date == day_str]
            day_obj = datetime.datetime.strptime(day_str, "%Y-%m-%d").date()
            day_label = day_obj.strftime("%A, %d %B %Y")
            
            is_today = (day_obj == datetime.date.today())
            badge_today = " 🌟 [TODAY]" if is_today else ""

            with st.expander(f"📅 **{day_label}** ({len(day_sessions)} sessions){badge_today}", expanded=(is_today or day_str == dates_in_view[0])):
                for sess in day_sessions:
                    card_class = "session-card-completed" if sess.completed else "session-card"
                    badge_type = "badge-review" if sess.session_type == SessionType.REVIEW else "badge-learning"

                    col_s1, col_s2, col_s3 = st.columns([5, 3, 2])
                    with col_s1:
                        st.markdown(f"""
                        <div class="{card_class}">
                            <span class="badge {badge_type}">{sess.session_type.value}</span>
                            <strong>{sess.subject_name}</strong>: {sess.topic_title}
                            <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px;">
                                🕒 <strong>{sess.time_slot}</strong> ({sess.duration_minutes} mins) |
                                ⚡ Cognitive Friction: <strong>{sess.cognitive_load_score}/5.0</strong>
                            </div>
                            <div style="font-size: 0.8rem; color: #cbd5e1; margin-top: 4px;">
                                📝 <em>{sess.notes or ''}</em>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col_s2:
                        if sess.completed:
                            st.success(f"✅ Completed\nRecall Quality: {sess.quality_rating or 4}/5")
                        else:
                            q_score = st.select_slider(
                                "SM-2 Quality Rating",
                                options=[0, 1, 2, 3, 4, 5],
                                value=4,
                                format_func=lambda x: {
                                    0: "0 - Blackout",
                                    1: "1 - Wrong, recalled later",
                                    2: "2 - Wrong, seemed easy",
                                    3: "3 - Correct, difficult",
                                    4: "4 - Correct, hesitating",
                                    5: "5 - Perfect recall"
                                }[x],
                                key=f"q_{sess.id}"
                            )

                    with col_s3:
                        if not sess.completed:
                            if st.button("Mark Complete", key=f"btn_done_{sess.id}", use_container_width=True):
                                st.session_state.orchestrator.mark_session_done(sess.id, quality_rating=q_score)
                                sess.completed = True
                                sess.quality_rating = q_score
                                st.toast(f"Session '{sess.topic_title}' marked complete!", icon="🎉")
                                st.rerun()


# ==========================================================
# TAB 2: CURRICULUM & KNOWLEDGE DAG
# ==========================================================
with tab_curriculum:
    st.markdown("### 📚 Syllabus Decomposition & Prerequisite Knowledge Graph")
    st.caption("Curriculum Agent uses Bloom's Cognitive Taxonomy to structure learning progressions.")

    if st.session_state.active_plan:
        plan = st.session_state.active_plan
        sel_subj = st.selectbox("Select Subject to Inspect", [s.name for s in plan.subjects])
        target_subj = next((s for s in plan.subjects if s.name == sel_subj), None)

        if target_subj:
            st.markdown(f"#### 🎯 {target_subj.name} (Exam Target: `{target_subj.target_exam_date}` | Priority: `{target_subj.priority}/5`)")
            
            # Display topics in structured table
            topics_data = []
            for t in target_subj.topics:
                prereqs = ", ".join(t.prerequisites) if t.prerequisites else "None (Foundational)"
                topics_data.append({
                    "Topic Title": t.title,
                    "Bloom's Taxonomy": t.bloom_level.value,
                    "Difficulty (1-5)": t.difficulty,
                    "Duration (mins)": t.estimated_minutes,
                    "Mastery Score": f"{int(t.mastery_score * 100)}%",
                    "Status": t.status.upper(),
                    "Prerequisite Dependencies": prereqs
                })

            df_topics = pd.DataFrame(topics_data)
            st.dataframe(df_topics, use_container_width=True)

            # Bloom taxonomy distribution chart
            st.markdown("##### Bloom's Taxonomy Cognitive Distribution")
            bloom_counts = pd.Series([t.bloom_level.value for t in target_subj.topics]).value_counts()
            st.bar_chart(bloom_counts)

    st.markdown("---")
    st.markdown("#### ➕ Add New Custom Subject with Curriculum Agent")
    with st.form("add_subject_form"):
        new_name = st.text_input("Subject Name", placeholder="e.g. Distributed Systems or Deep Learning")
        new_exam = st.date_input("Target Exam Date", value=datetime.date.today() + datetime.timedelta(days=30))
        new_priority = st.slider("Priority Level (1: Low, 5: Critical)", 1, 5, 4)
        new_syllabus = st.text_area("Paste Raw Syllabus Text / Topic List", placeholder="- Topic 1: Architecture\n- Topic 2: Consensus Algorithms\n- Topic 3: Sharding & Replication", height=120)
        submit_add = st.form_submit_button("🤖 Deconstruct & Append to Active Plan")

        if submit_add and new_name and new_syllabus:
            with st.spinner("Curriculum Agent analyzing topics & prerequisites..."):
                res = st.session_state.orchestrator.curriculum_agent.execute({
                    "subject_name": new_name,
                    "raw_syllabus_text": new_syllabus,
                    "target_exam_date": new_exam.strftime("%Y-%m-%d"),
                    "priority": new_priority
                })
                new_subj_obj = res["subject"]
                if st.session_state.active_plan:
                    st.session_state.active_plan.subjects.append(new_subj_obj)
                    # Re-run scheduler
                    sched_res = st.session_state.orchestrator.scheduling_agent.execute({
                        "plan_id": st.session_state.active_plan.id,
                        "profile": st.session_state.active_plan.profile,
                        "subjects": st.session_state.active_plan.subjects,
                        "include_spaced_reviews": True
                    })
                    st.session_state.active_plan.sessions = sched_res["sessions"]
                    st.session_state.db.save_study_plan(st.session_state.active_plan)
                    st.success(f"Added {new_name} and generated {len(sched_res['sessions'])} updated sessions!")
                    st.rerun()


# ==========================================================
# TAB 3: SPACED REPETITION (SM-2)
# ==========================================================
with tab_sm2:
    st.markdown("### 🧠 SuperMemo-2 (SM-2) Spaced Repetition Engine")
    st.caption("Active recall flashcard review system implementing the mathematical SM-2 interval algorithm.")

    all_cards = st.session_state.db.get_all_flashcards()
    due_cards = st.session_state.db.get_due_flashcards()

    c_m1, c_m2, c_m3 = st.columns(3)
    with c_m1:
        st.metric("Total Flashcards in Deck", len(all_cards))
    with c_m2:
        st.metric("Cards Due for Review Today", len(due_cards))
    with c_m3:
        avg_ef = round(sum(c.easiness_factor for c in all_cards) / max(1, len(all_cards)), 2) if all_cards else 2.5
        st.metric("Deck Avg Easiness Factor (EF)", avg_ef)

    if not all_cards:
        st.info("No flashcards found. Generate them from the Curriculum or Load the Demo CSE plan.")
    else:
        # Active Review Deck
        deck_to_review = due_cards if due_cards else all_cards
        st.session_state.flashcard_index = min(st.session_state.flashcard_index, len(deck_to_review) - 1)
        current_card = deck_to_review[st.session_state.flashcard_index]

        st.markdown(f"#### Card {st.session_state.flashcard_index + 1} of {len(deck_to_review)}: **{current_card.subject_name}** (`{current_card.topic_title}`)")

        # Card Container
        if not st.session_state.show_flashcard_answer:
            st.markdown(f"""
            <div class="flashcard-box" style="border-color: #3b82f6;">
                <div>
                    <span style="font-size: 0.85rem; color: #93c5fd; text-transform: uppercase;">PROMPT / QUESTION</span><br><br>
                    {current_card.front}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("💡 Show Answer (Flip Card)", use_container_width=True, type="primary"):
                st.session_state.show_flashcard_answer = True
                st.rerun()
        else:
            st.markdown(f"""
            <div class="flashcard-box" style="border-color: #10b981;">
                <div>
                    <span style="font-size: 0.85rem; color: #6ee7b7; text-transform: uppercase;">ANSWER / INVARIANT</span><br><br>
                    {current_card.back}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("##### Rate Recall Quality (SM-2 $q \\in [0, 5]$):")
            st.caption("How accurately and effortlessly did you recall the answer?")

            col_q0, col_q1, col_q2, col_q3, col_q4, col_q5 = st.columns(6)

            with col_q0:
                if st.button("0: Blackout", use_container_width=True):
                    st.session_state.orchestrator.review_flashcard_sm2(current_card, 0)
                    st.session_state.show_flashcard_answer = False
                    st.session_state.flashcard_index = (st.session_state.flashcard_index + 1) % len(deck_to_review)
                    st.rerun()
            with col_q1:
                if st.button("1: Incorrect", use_container_width=True):
                    st.session_state.orchestrator.review_flashcard_sm2(current_card, 1)
                    st.session_state.show_flashcard_answer = False
                    st.session_state.flashcard_index = (st.session_state.flashcard_index + 1) % len(deck_to_review)
                    st.rerun()
            with col_q2:
                if st.button("2: Hard Fail", use_container_width=True):
                    st.session_state.orchestrator.review_flashcard_sm2(current_card, 2)
                    st.session_state.show_flashcard_answer = False
                    st.session_state.flashcard_index = (st.session_state.flashcard_index + 1) % len(deck_to_review)
                    st.rerun()
            with col_q3:
                if st.button("3: Pass (Hard)", use_container_width=True):
                    st.session_state.orchestrator.review_flashcard_sm2(current_card, 3)
                    st.session_state.show_flashcard_answer = False
                    st.session_state.flashcard_index = (st.session_state.flashcard_index + 1) % len(deck_to_review)
                    st.rerun()
            with col_q4:
                if st.button("4: Good", use_container_width=True):
                    st.session_state.orchestrator.review_flashcard_sm2(current_card, 4)
                    st.session_state.show_flashcard_answer = False
                    st.session_state.flashcard_index = (st.session_state.flashcard_index + 1) % len(deck_to_review)
                    st.rerun()
            with col_q5:
                if st.button("5: Perfect", use_container_width=True, type="primary"):
                    st.session_state.orchestrator.review_flashcard_sm2(current_card, 5)
                    st.session_state.show_flashcard_answer = False
                    st.session_state.flashcard_index = (st.session_state.flashcard_index + 1) % len(deck_to_review)
                    st.rerun()

            st.write("")
            st.info(f"📊 **Current SM-2 Metrics**: Streak $n$ = `{current_card.repetition_number}`, Easiness Factor $EF$ = `{current_card.easiness_factor}`, Current Interval $I$ = `{current_card.interval_days} days`, Next Review = `{current_card.next_review_date}`")


# ==========================================================
# TAB 4: DIAGNOSTIC QUIZ & ASSESSMENT
# ==========================================================
with tab_quiz:
    st.markdown("### 🎯 Dynamic Diagnostic Quiz & Knowledge Mastery Agent")
    st.caption("Assessment Agent validates Bloom's level understanding and automatically injects remedial sessions if score < 60%.")

    if not st.session_state.active_plan:
        st.warning("Please load or create a study plan to take diagnostic quizzes.")
    else:
        plan = st.session_state.active_plan
        all_topics_list = []
        for s in plan.subjects:
            all_topics_list.extend(s.topics)

        topic_options = {f"[{t.subject_name}] {t.title}": t for t in all_topics_list}
        selected_key = st.selectbox("Select Topic to Test", list(topic_options.keys()))
        chosen_topic = topic_options[selected_key]

        col_qg1, col_qg2 = st.columns([3, 1])
        with col_qg1:
            st.markdown(f"**Topic**: `{chosen_topic.title}` | **Bloom Level**: `{chosen_topic.bloom_level.value}` | **Difficulty**: `{chosen_topic.difficulty}/5`")
        with col_qg2:
            if st.button("Generate Diagnostic Quiz", type="primary", use_container_width=True):
                with st.spinner("Assessment Agent synthesizing contextual MCQs..."):
                    questions = st.session_state.orchestrator.generate_quiz_for_topic(chosen_topic, num_questions=3)
                    st.session_state.current_quiz_questions = questions
                    st.session_state.quiz_active_topic = chosen_topic
                    st.rerun()

        # Render Active Quiz
        if st.session_state.current_quiz_questions and st.session_state.quiz_active_topic:
            st.markdown("---")
            q_list = st.session_state.current_quiz_questions
            user_answers = {}

            with st.form("diagnostic_quiz_form"):
                for idx, q in enumerate(q_list):
                    st.markdown(f"**Question {idx + 1}** (`Bloom: {q.bloom_level.value}`)")
                    st.write(q.question)
                    user_choice = st.radio(
                        "Choose the best answer:",
                        options=list(range(len(q.options))),
                        format_func=lambda i: q.options[i],
                        key=f"mcq_{q.id}"
                    )
                    user_answers[q.id] = user_choice
                    st.write("")

                submit_quiz = st.form_submit_button("Submit Quiz for Agent Evaluation", type="primary")

                if submit_quiz:
                    with st.spinner("Evaluating submission and checking cognitive mastery..."):
                        eval_res = st.session_state.orchestrator.submit_quiz_answers(
                            topic=st.session_state.quiz_active_topic,
                            questions=q_list,
                            user_answers=user_answers,
                            active_plan=st.session_state.active_plan
                        )

                        if eval_res.percentage >= 80:
                            st.balloons()
                            st.success(f"🎉 Score: {eval_res.score}/{eval_res.total_questions} ({eval_res.percentage}%)\n{eval_res.feedback}")
                        elif eval_res.percentage >= 60:
                            st.info(f"👍 Score: {eval_res.score}/{eval_res.total_questions} ({eval_res.percentage}%)\n{eval_res.feedback}")
                        else:
                            st.error(f"⚠️ Score: {eval_res.score}/{eval_res.total_questions} ({eval_res.percentage}%)\n{eval_res.feedback}")
                            st.warning(f"🚨 **Closed-Loop Action**: {eval_res.recommended_action}")

                        # Show explanations
                        for idx, q in enumerate(q_list):
                            st.markdown(f"**Q{idx+1} Explanation**: {q.explanation} (Correct: *{q.options[q.correct_option_index]}*)")


# ==========================================================
# TAB 5: FOCUS POMODORO TIMER
# ==========================================================
with tab_pomodoro:
    st.markdown("### ⏱️ Cognitive Flow & Pomodoro Focus Timer")
    st.caption("Aligned with your chronotype to maximize sustained attention and prevent cognitive fatigue.")

    c_p1, c_p2 = st.columns([2, 1])
    with c_p1:
        timer_mode = st.radio("Focus Mode", ["Deep Work (50 mins)", "Standard Focus (25 mins)", "Short Rest (5 mins)", "Long Rest (15 mins)"], horizontal=True)
        minutes_map = {
            "Deep Work (50 mins)": 50,
            "Standard Focus (25 mins)": 25,
            "Short Rest (5 mins)": 5,
            "Long Rest (15 mins)": 15
        }
        timer_min = minutes_map[timer_mode]

        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.8); border: 2px solid #6366f1; border-radius: 20px; padding: 40px; text-align: center; margin: 20px 0;">
            <div style="font-size: 5rem; font-family: monospace; font-weight: 700; color: #38bdf8;">
                {timer_min:02d}:00
            </div>
            <div style="font-size: 1.1rem; color: #94a3b8; margin-top: 10px;">
                Mode: {timer_mode} | Distraction-free Study Block
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.button("▶️ Start Focus Session", use_container_width=True, type="primary")
        with col_t2:
            st.button("⏹️ Reset Timer", use_container_width=True)

    with c_p2:
        st.markdown("#### 💡 Cognitive Flow Tips")
        st.info("""
        - **Monotasking**: Close all unrelated tabs and notifications.
        - **Active Retrieval**: Write summaries in your own words rather than passive re-reading.
        - **Hydration**: Drink 250ml water between focus blocks.
        - **Chronotype Sync**: Schedule complex algorithm topics during your peak energy hours.
        """)


# ==========================================================
# TAB 6: COGNITIVE ANALYTICS & METRICS
# ==========================================================
with tab_analytics:
    st.markdown("### 📈 Learning Analytics & Ebbinghaus Retention Modeling")
    st.caption("Quantitative tracking of session completion, subject workload balance, and memory stability.")

    analytics = st.session_state.db.get_completion_analytics()

    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.markdown("#### 📊 Subject Workload Allocation (Sessions)")
        if analytics["subject_distribution"]:
            df_subj = pd.DataFrame(list(analytics["subject_distribution"].items()), columns=["Subject", "Sessions"])
            st.bar_chart(df_subj.set_index("Subject"))
        else:
            st.info("No session distribution data available yet.")

    with col_a2:
        st.markdown("#### 🧠 Ebbinghaus Forgetting Curve Simulator")
        st.caption("Memory Retention Probability $R(t) = e^{-t / (2 \\cdot EF)}$ over 30 Days")

        days_axis = np.arange(0, 31, 1)
        # Without Spaced Repetition (EF = 1.3, baseline drop)
        retention_without_sr = [math.exp(-d / 2.6) * 100 for d in days_axis]
        # With SM-2 Spaced Repetition (EF = 2.5, periodic reinforcement)
        retention_with_sr = []
        for d in days_axis:
            if d < 1:
                retention_with_sr.append(100)
            elif d < 6:
                retention_with_sr.append(max(65, math.exp(-(d % 3) / 5.0) * 100))
            elif d < 16:
                retention_with_sr.append(max(75, math.exp(-(d % 6) / 8.0) * 100))
            else:
                retention_with_sr.append(max(85, math.exp(-(d % 14) / 15.0) * 100))

        df_ebbinghaus = pd.DataFrame({
            "Days Elapsed": days_axis,
            "Standard Forgetting (No Reviews)": retention_without_sr,
            "AetherPlan SM-2 Spaced Repetition": retention_with_sr
        }).set_index("Days Elapsed")

        st.line_chart(df_ebbinghaus)

    # Quiz Diagnostic Historical Log
    st.markdown("#### 📝 Diagnostic Assessment History")
    quizzes = st.session_state.db.get_all_quiz_results()
    if quizzes:
        q_history = []
        for q in quizzes:
            q_history.append({
                "Timestamp": q.timestamp,
                "Topic": q.topic_title,
                "Score": f"{q.score}/{q.total_questions}",
                "Percentage": f"{q.percentage}%",
                "Diagnostic Feedback": q.feedback
            })
        st.dataframe(pd.DataFrame(q_history), use_container_width=True)
    else:
        st.info("No quiz results logged yet. Complete a quiz in the Diagnostic Quiz tab.")


# ==========================================================
# TAB 7: AGENT THOUGHT TRACES
# ==========================================================
with tab_traces:
    st.markdown("### 🤖 Multi-Agent Reasoning Audit Trail")
    st.caption("Live inspectable Thought-Action traces recorded across all autonomous agents.")

    logs = st.session_state.orchestrator.get_all_agent_logs()

    if not logs:
        st.info("No agent reasoning logs recorded in the current session. Run a plan or quiz to view live traces.")
    else:
        st.markdown(f"Total Logged Reasoning Steps: `{len(logs)}`")
        for log in reversed(logs[-25:]):
            agent_color = {
                "Curriculum Agent": "#38bdf8",
                "Cognitive Agent": "#a855f7",
                "Scheduling Agent": "#10b981",
                "Retention Agent": "#f59e0b",
                "Assessment Agent": "#ec4899",
                "Rescheduler Agent": "#ef4444"
            }.get(log["agent"], "#cbd5e1")

            st.markdown(f"""
            <div class="thought-trace" style="border-left-color: {agent_color};">
                <span style="color: {agent_color}; font-weight: bold;">[{log['agent']} - {log['role']}]</span>
                <span style="color: #64748b; font-size: 0.75rem; float: right;">{log['timestamp']}</span><br>
                <span style="color: #94a3b8; font-weight: 600;">Action:</span> <code>{log['action']}</code><br>
                <span style="color: #cbd5e1;">Thought:</span> {log['thought']}
            </div>
            """, unsafe_allow_html=True)
