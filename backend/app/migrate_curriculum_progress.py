import sys
import os
import json
import sqlite3

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.database import SessionLocal
from backend.app.models.material import LearningMaterial
from backend.app.models.material_topic import MaterialTopic
from backend.app.models.attempt import QuizAttempt
from backend.app.models.quiz import Quiz
from backend.app.services.curriculum_extractor import extract_curriculum_topics
from backend.app.services.subject_progress_service import (
    get_or_create_subject_definition,
    compute_user_subject_progress,
    sync_subject_progress_record
)


def preview_and_migrate(apply: bool = False, target_user_id: str = "3"):
    db = SessionLocal()
    print(f"=== CURRICULUM & PROGRESS MIGRATION (apply={apply}, user_id={target_user_id}) ===")

    materials = db.query(LearningMaterial).filter(LearningMaterial.user_id == target_user_id).all()
    if not materials:
        print(f"No materials found for user {target_user_id}.")
        db.close()
        return

    for mat in materials:
        print(f"\n[MATERIAL ID {mat.id}] Title: '{mat.title}' | Subject: '{mat.subject_code}' | File: '{mat.file_name}'")
        
        # Extract or inspect curriculum
        curriculum = extract_curriculum_topics(
            db=db,
            material_id=mat.id,
            user_id=target_user_id,
            subject_code=mat.subject_code,
            force_refresh=True  # Ensure fresh extraction from genuine material headings
        )

        chapters = curriculum.get("chapters", [])
        print(f"\n---> NEW EXTRACTED CURRICULUM STRUCTURE ({len(chapters)} chapters):")
        total_topics = 0
        for c_idx, ch in enumerate(chapters, 1):
            print(f"\n  Chapter {c_idx}: {ch['title']}")
            for t_idx, tp in enumerate(ch.get("topics", []), 1):
                total_topics += 1
                mins = tp.get("estimatedMinutes", 15)
                summary = tp.get("summary", "")[:75]
                print(f"    {c_idx}.{t_idx} {tp['title']} ({mins} mins)")
                print(f"         Summary: {summary}...")

        print(f"\nTotal Topics in Material: {total_topics}")

        # Compute progress under the new formula
        subj_def = get_or_create_subject_definition(mat.subject_code)
        new_progress = compute_user_subject_progress(db, user_id=target_user_id, subject_def=subj_def)

        print("\n---> NEW PROGRESS CALCULATION FOR COA:")
        print(f"  * Status: {new_progress['status']}")
        print(f"  * Progress Percent: {new_progress['progress_percent']}%")
        print(f"  * Current Topic: {new_progress['current_topic']}")
        print(f"  * Topics Mastered: {new_progress['topics_completed']} / {new_progress['total_topics']}")
        print(f"  * Chapters Count: {len(new_progress['chapters'])}")

        print("\n---> DETAILED TOPIC STATUS BREAKDOWN:")
        for ch in new_progress["chapters"]:
            print(f"  [{ch['status'].upper()}] Chapter: {ch['title']}")
            for t in ch.get("topics", []):
                score_str = f"Best: {t['best_score']}%" if t['best_score'] is not None else "No score"
                print(f"    - {t['title']}: Status='{t['status_label']}' (Credit: {t['credit_percent']}%) | Quizzes: {t['quiz_attempts_count']} | {score_str} | Read: {t['has_read']}")

        if apply:
            print("\n--> APPLYING NEW PROGRESS TO DATABASE...")
            sync_subject_progress_record(db, user_id=target_user_id, subject_def=subj_def, progress_data=new_progress)
            print("--> SUCCESS: Progress successfully synchronized in SQLite!")
        else:
            print("\n[PREVIEW MODE] No database changes committed. Waiting for user confirmation to apply.")

    db.close()


if __name__ == "__main__":
    apply_mode = "--apply" in sys.argv
    preview_and_migrate(apply=apply_mode, target_user_id="3")

