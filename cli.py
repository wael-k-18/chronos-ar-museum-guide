"""
Command Line Interface (CLI) Runner for AetherPlan AAI
Author: CSE Engineering PBL Team
"""

import os
import sys
import datetime
from core.models import StudentProfile, Chronotype
from core.database import DatabaseManager
from agents.orchestrator import StudyPlannerOrchestrator


def print_banner():
    print("=" * 70)
    print("  🧠 AETHERPLAN AAI: AUTONOMOUS STUDY PLANNER AGENT")
    print("  Final Year CSE Engineering Project-Based Learning (PBL)")
    print("=" * 70)


def main():
    print_banner()
    db = DatabaseManager()
    orchestrator = StudyPlannerOrchestrator(db_manager=db)

    while True:
        print("\n--- Main Menu ---")
        print("1. Generate Demo Final Year CSE Study Plan (Multi-Agent Workflow)")
        print("2. View Current Study Plan & Sessions")
        print("3. View / Review Spaced Repetition (SM-2) Flashcards")
        print("4. Take Diagnostic Assessment Quiz for a Topic")
        print("5. Trigger Reflexion & Adaptive Rescheduling")
        print("6. Inspect Multi-Agent Reasoning Thought Traces")
        print("7. Launch Streamlit Web UI")
        print("8. Exit")

        choice = input("\nEnter choice [1-8]: ").strip()

        if choice == "1":
            print("\n[Orchestrator] Invoking Curriculum, Cognitive, Scheduling & Retention Agents...")
            profile = StudentProfile(
                name="Alex Mercer",
                semester="Semester 8",
                branch="Computer Science & Engineering",
                daily_available_hours=4.0,
                chronotype=Chronotype.BALANCED
            )
            subjects = [
                {
                    "name": "Operating Systems",
                    "priority": 5,
                    "exam_date": (datetime.date.today() + datetime.timedelta(days=21)).strftime("%Y-%m-%d"),
                    "syllabus": "Process Management, CPU Scheduling, Synchronization & Semaphores, Deadlock & Banker's Algorithm, Virtual Memory Paging"
                },
                {
                    "name": "Machine Learning",
                    "priority": 4,
                    "exam_date": (datetime.date.today() + datetime.timedelta(days=28)).strftime("%Y-%m-%d"),
                    "syllabus": "Linear Regression, Logistic Regression, Decision Trees, Support Vector Machines, K-Means Clustering, Neural Networks & Backprop"
                }
            ]
            plan = orchestrator.create_complete_study_plan(
                title="CSE Final Year Engineering Core Curriculum",
                subject_data=subjects,
                profile=profile,
                exam_target_date=(datetime.date.today() + datetime.timedelta(days=28)).strftime("%Y-%m-%d")
            )
            print(f"✨ Plan Created Successfully: ID={plan.id}")
            print(f"   Total Sessions Generated: {len(plan.sessions)}")
            print(f"   Total Subjects: {len(plan.subjects)}")

        elif choice == "2":
            plan = db.get_latest_active_plan()
            if not plan:
                print("⚠️ No active plan found. Please generate a plan first (Option 1).")
                continue
            print(f"\nPlan: {plan.title} (Target: {plan.exam_target_date})")
            print(f"Daily Available Hours: {plan.profile.daily_available_hours}h | Chronotype: {plan.profile.chronotype.value}")
            print("\nFirst 10 Scheduled Sessions:")
            print("-" * 70)
            for idx, s in enumerate(plan.sessions[:10]):
                status = "COMPLETED" if s.completed else "PENDING"
                print(f"[{idx+1:02d}] {s.scheduled_date} | {s.time_slot} | {s.subject_name:18} | {s.session_type.value:8} | {s.topic_title} [{status}]")
            print("-" * 70)

        elif choice == "3":
            due_cards = db.get_due_flashcards()
            if not due_cards:
                due_cards = db.get_all_flashcards()
            if not due_cards:
                print("⚠️ No flashcards in deck. Generate a plan first (Option 1).")
                continue
            card = due_cards[0]
            print(f"\n--- Flashcard: {card.subject_name} ({card.topic_title}) ---")
            print(f"Front Prompt: {card.front}")
            input("Press Enter to reveal answer...")
            print(f"Back Answer:  {card.back}")
            print("\nRate recall quality (0=Blackout, 3=Pass with difficulty, 5=Perfect recall):")
            try:
                q = int(input("Quality [0-5]: ").strip())
                updated = orchestrator.review_flashcard_sm2(card, q)
                print(f"✨ SM-2 Updated: Interval={updated.interval_days} days, EF={updated.easiness_factor}, Next Review={updated.next_review_date}")
            except Exception as e:
                print("Invalid input, skipping review.")

        elif choice == "4":
            plan = db.get_latest_active_plan()
            if not plan:
                print("⚠️ No active plan found. Please generate a plan first.")
                continue
            all_topics = []
            for s in plan.subjects:
                all_topics.extend(s.topics)
            print("\nAvailable Topics:")
            for idx, t in enumerate(all_topics[:6]):
                print(f"[{idx+1}] {t.subject_name}: {t.title}")
            try:
                pick = int(input("Select topic index: ").strip()) - 1
                topic = all_topics[pick]
                questions = orchestrator.generate_quiz_for_topic(topic, num_questions=2)
                answers = {}
                for q_idx, q in enumerate(questions):
                    print(f"\nQ{q_idx+1}: {q.question}")
                    for o_idx, opt in enumerate(q.options):
                        print(f"  [{o_idx}] {opt}")
                    ans = int(input("Your choice [0-3]: ").strip())
                    answers[q.id] = ans
                eval_res = orchestrator.submit_quiz_answers(topic, questions, answers, active_plan=plan)
                print(f"\n--- Diagnostic Result ---")
                print(f"Score: {eval_res.score}/{eval_res.total_questions} ({eval_res.percentage}%)")
                print(f"Feedback: {eval_res.feedback}")
                print(f"Action:   {eval_res.recommended_action}")
            except Exception as e:
                print("Quiz interaction cancelled or invalid input.")

        elif choice == "5":
            plan = db.get_latest_active_plan()
            if not plan:
                print("⚠️ No active plan found.")
                continue
            print("[Rescheduler Agent] Checking for schedule slip and overdue sessions...")
            healed = orchestrator.trigger_adaptive_rescheduling(plan)
            print("✨ Schedule rebalanced and committed to database.")

        elif choice == "6":
            logs = orchestrator.get_all_agent_logs()
            print(f"\n--- Multi-Agent Reasoning Traces (Total: {len(logs)}) ---")
            for l in logs[-10:]:
                print(f"[{l['timestamp']}] {l['agent']} ({l['action']}):")
                print(f"   Thought: {l['thought']}")

        elif choice == "7":
            print("Launching Streamlit Web UI...")
            os.system("streamlit run app.py")

        elif choice == "8":
            print("Exiting AetherPlan AAI. Goodbye!")
            sys.exit(0)


if __name__ == "__main__":
    main()
