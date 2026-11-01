import sqlite3
import os
import sys

DB_PATH = "backend/edumind.db"

def inspect_and_cleanup(dry_run=True, target_user_id="3"):
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print(f"=== DATABASE INSPECTION & CLEANUP (dry_run={dry_run}, user_id={target_user_id}) ===")

    # 1. Check Learning Materials for target user
    materials = cur.execute(
        "SELECT id, user_id, title, subject_code, file_name, created_at FROM learning_materials WHERE user_id = ?",
        (target_user_id,)
    ).fetchall()
    print(f"\n[KEEP SAFE] Legitimate uploaded materials for User {target_user_id}:")
    for m in materials:
        print(f"  - Material ID {m['id']}: '{m['title']}' | File: '{m['file_name']}' | Subject: '{m['subject_code']}'")

    # 2. Check Subject Progress rows for target user
    sp_rows = cur.execute(
        "SELECT id, user_id, subject_code, subject_slug, status, progress_percent, current_topic, topics_completed, total_topics FROM subject_progress WHERE user_id = ?",
        (target_user_id,)
    ).fetchall()
    
    # 3. Check Quizzes and Attempts for target user
    quizzes = cur.execute(
        "SELECT id, user_id, material_id, title, subject_code, topic, total_questions FROM quizzes WHERE user_id = ?",
        (target_user_id,)
    ).fetchall()

    attempts = cur.execute(
        "SELECT id, user_id, quiz_id, status, score_percentage, correct_count, total_questions FROM quiz_attempts WHERE user_id = ?",
        (target_user_id,)
    ).fetchall()

    topic_comps = cur.execute(
        "SELECT id, user_id, subject_code, topic_title, completed_at FROM topic_completions WHERE user_id = ?",
        (target_user_id,)
    ).fetchall()

    print(f"\n[CANDIDATES FOR CLEANUP / RESET] Found for User {target_user_id}:")
    print(f"\n1. Subject Progress rows ({len(sp_rows)} found):")
    for sp in sp_rows:
        reason = ""
        if sp["subject_code"] == "CS301":
            reason = "Dummy / seed 'Data Structures' with 0 uploaded files"
        elif sp["subject_code"] in ("B3EN", "B5CS"):
            reason = "Residual test record with 0 uploaded files"
        elif sp["subject_code"] == "B3C":
            reason = "Duplicate acronym collision generated from 'BCS 301 - COA'"
        else:
            reason = "Residual progress entry"
        print(f"  - SubjectProgress ID {sp['id']}: Code='{sp['subject_code']}', Slug='{sp['subject_slug']}', Status='{sp['status']}', Progress={sp['progress_percent']}% -> REASON: {reason}")

    print(f"\n2. Auto-completed Topics ({len(topic_comps)} found):")
    for tc in topic_comps:
        print(f"  - TopicCompletion ID {tc['id']}: Subject='{tc['subject_code']}', Topic='{tc['topic_title']}' -> REASON: Erroneously auto-completed on 20% quiz score")

    print(f"\n3. Test Quiz Attempts ({len(attempts)} found):")
    for att in attempts:
        print(f"  - QuizAttempt ID {att['id']}: Quiz ID {att['quiz_id']}, Status='{att['status']}', Score={att['score_percentage']}% -> REASON: Reset test attempts so COA starts with clean slate 0%")

    print(f"\n4. Test Quizzes ({len(quizzes)} found):")
    for q in quizzes:
        print(f"  - Quiz ID {q['id']}: Title='{q['title']}', Subject='{q['subject_code']}', Topic='{q['topic_topic'] if 'topic_topic' in q.keys() else q['topic']}' -> Generated during testing")

    if not dry_run:
        print("\n--> EXECUTING CLEANUP...")
        # Delete dummy subject_progress for User 3
        cur.execute("DELETE FROM subject_progress WHERE user_id = ?", (target_user_id,))
        # Delete topic_completions for User 3
        cur.execute("DELETE FROM topic_completions WHERE user_id = ?", (target_user_id,))
        # Delete quiz attempts for User 3
        cur.execute("DELETE FROM quiz_attempts WHERE user_id = ?", (target_user_id,))
        # Delete quizzes for User 3
        cur.execute("DELETE FROM quizzes WHERE user_id = ?", (target_user_id,))
        conn.commit()
        print("--> CLEANUP EXECUTED SUCCESSFULLY! Database updated.")
    else:
        print("\n[DRY RUN MODE] No records were modified or deleted. Waiting for user confirmation.")

    conn.close()

if __name__ == "__main__":
    is_dry = "--execute" not in sys.argv
    target_user = "3"
    for arg in sys.argv:
        if arg.startswith("--user="):
            target_user = arg.split("=")[1]
    inspect_and_cleanup(dry_run=is_dry, target_user_id=target_user)

