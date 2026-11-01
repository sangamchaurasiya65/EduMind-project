import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.material import LearningMaterial
from backend.app.models.quiz import Quiz, QuizQuestion
from backend.app.models.attempt import QuizAttempt, LearnerResponse
from backend.app.models.study_session import StudySession
from backend.app.models.subject_progress import SubjectProgress
from backend.app.models.topic_completion import TopicCompletion
from backend.app.models.activity_log import UserActivityLog



# Curated vibrant colors palette for dynamically created subjects
PALETTE = [
    ("#4f46e5", "#eef2ff"),  # Indigo
    ("#7c3aed", "#f5f3ff"),  # Violet
    ("#0ea5e9", "#f0f9ff"),  # Sky
    ("#10b981", "#ecfdf5"),  # Emerald
    ("#f59e0b", "#fffbeb"),  # Amber
    ("#ec4899", "#fdf2f8"),  # Pink
    ("#06b6d4", "#ecfeff"),  # Cyan
    ("#8b5cf6", "#f3e8ff"),  # Purple
    ("#14b8a6", "#f0fdf4")   # Teal
]


# Standard curriculum syllabus templates for core subjects
SUBJECT_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "id": "data-structures",
        "name": "Data Structures",
        "code": "CS301",
        "aliases": ["CS301", "DATA-STRUCTURES", "DATA STRUCTURES", "DSA"],
        "description": "Linear and non-linear data structures, arrays, linked lists, stacks, queues, trees, and sorting techniques.",
        "color": "#4f46e5",
        "bg": "#eef2ff",
        "chapters": [
            {"id": 1, "title": "Introduction to Data Structures", "duration": "45 mins"},
            {"id": 2, "title": "Arrays & Strings", "duration": "1.2 hrs"},
            {"id": 3, "title": "Stacks & Queues", "duration": "1.5 hrs"},
            {"id": 4, "title": "Linked Lists", "duration": "2.0 hrs"},
            {"id": 5, "title": "Trees & Binary Search Trees", "duration": "2.5 hrs"},
            {"id": 6, "title": "Searching & Sorting Techniques", "duration": "3.0 hrs"}
        ]
    },
    {
        "id": "database-management",
        "name": "Database Management",
        "code": "CS303",
        "aliases": ["CS303", "DATABASE-MANAGEMENT", "DATABASE MANAGEMENT", "DBMS"],
        "description": "Relational database concepts, ER modeling, SQL querying, Normalization, and transaction management.",
        "color": "#7c3aed",
        "bg": "#f5f3ff",
        "chapters": [
            {"id": 1, "title": "Introduction to DBMS", "duration": "1.0 hr"},
            {"id": 2, "title": "Entity-Relationship (ER) Modeling", "duration": "1.5 hrs"},
            {"id": 3, "title": "SQL Basics & Queries", "duration": "2.0 hrs"},
            {"id": 4, "title": "Joins, Subqueries & Views", "duration": "1.8 hrs"},
            {"id": 5, "title": "Database Normalization (1NF - BCNF)", "duration": "2.5 hrs"},
            {"id": 6, "title": "Transaction & Concurrency Control", "duration": "2.2 hrs"}
        ]
    },
    {
        "id": "computer-networks",
        "name": "Computer Networks",
        "code": "CS305",
        "aliases": ["CS305", "COMPUTER-NETWORKS", "COMPUTER NETWORKS", "CN"],
        "description": "Layered architecture, OSI and TCP/IP models, data link framing, routing algorithms, and transport protocols.",
        "color": "#0ea5e9",
        "bg": "#f0f9ff",
        "chapters": [
            {"id": 1, "title": "Network Fundamentals", "duration": "1.5 hrs"},
            {"id": 2, "title": "OSI vs TCP/IP Layer Models", "duration": "1.8 hrs"},
            {"id": 3, "title": "Data Link Layer & Error Detection", "duration": "2.0 hrs"},
            {"id": 4, "title": "Network Layer & IP Addressing", "duration": "2.5 hrs"},
            {"id": 5, "title": "Transport Layer: TCP & UDP", "duration": "2.0 hrs"},
            {"id": 6, "title": "Application Protocols & Security", "duration": "1.5 hrs"}
        ]
    },
    {
        "id": "operating-systems",
        "name": "Operating Systems",
        "code": "CS304",
        "aliases": ["CS304", "OPERATING-SYSTEMS", "OPERATING SYSTEMS", "OS"],
        "description": "Process synchronization, CPU scheduling algorithms, deadlock prevention, and virtual memory management.",
        "color": "#10b981",
        "bg": "#ecfdf5",
        "chapters": [
            {"id": 1, "title": "Introduction to Operating Systems", "duration": "1.0 hr"},
            {"id": 2, "title": "Processes & Threads", "duration": "1.5 hrs"},
            {"id": 3, "title": "Process Management & CPU Scheduling", "duration": "2.0 hrs"},
            {"id": 4, "title": "Process Synchronization & Semaphores", "duration": "2.2 hrs"},
            {"id": 5, "title": "Deadlocks & Banker's Algorithm", "duration": "1.8 hrs"},
            {"id": 6, "title": "Virtual Memory & Paging", "duration": "2.5 hrs"}
        ]
    },
    {
        "id": "computer-organization",
        "name": "Computer Organization",
        "code": "CS302",
        "aliases": ["CS302", "COMPUTER-ORGANIZATION", "COMPUTER ORGANIZATION", "COA", "SOFTWARE-ENGINEERING"],
        "description": "Instruction set architecture (ISA), computer arithmetic, ALU design, memory hierarchy, cache, and pipelining.",
        "color": "#059669",
        "bg": "#ecfdf5",
        "chapters": [
            {"id": 1, "title": "Digital Logic & Data Representation", "duration": "1.2 hrs"},
            {"id": 2, "title": "Register Transfer & Micro-operations", "duration": "1.5 hrs"},
            {"id": 3, "title": "Basic Computer Organization & Design", "duration": "2.0 hrs"},
            {"id": 4, "title": "Central Processing Unit & Pipelining", "duration": "2.5 hrs"},
            {"id": 5, "title": "Memory Hierarchy & Cache Mapping", "duration": "2.0 hrs"},
            {"id": 6, "title": "Input-Output Organization (DMA & Interrupts)", "duration": "1.5 hrs"}
        ]
    },
    {
        "id": "mathematics",
        "name": "Mathematics",
        "code": "MA301",
        "aliases": ["MA301", "MATH201", "MATHEMATICS", "ENGINEERING-MATHEMATICS", "MATHS"],
        "description": "Higher engineering mathematics including differential equations, linear algebra, matrices, and probability.",
        "color": "#d97706",
        "bg": "#fffbeb",
        "chapters": [
            {"id": 1, "title": "Matrices & Linear Equations", "duration": "2.0 hrs"},
            {"id": 2, "title": "Differential Equations", "duration": "2.5 hrs"},
            {"id": 3, "title": "Partial Differential Equations", "duration": "2.0 hrs"},
            {"id": 4, "title": "Multiple Integrals & Vector Calculus", "duration": "3.0 hrs"},
            {"id": 5, "title": "Fourier Series & Transforms", "duration": "2.8 hrs"},
            {"id": 6, "title": "Probability & Statistics", "duration": "2.5 hrs"}
        ]
    }
]

# Quick lookup mapping from code or slug to template definition
CODE_OR_SLUG_MAP: Dict[str, Dict[str, Any]] = {}
for subj in SUBJECT_DEFINITIONS:
    CODE_OR_SLUG_MAP[subj["code"].upper()] = subj
    CODE_OR_SLUG_MAP[subj["id"].lower()] = subj
    for alias in subj["aliases"]:
        CODE_OR_SLUG_MAP[alias.upper()] = subj
        CODE_OR_SLUG_MAP[alias.lower()] = subj


def slugify(text: str) -> str:
    """Converts a subject name or code to a URL-friendly slug."""
    s = re.sub(r'[^a-zA-Z0-9]+', '-', text.strip().lower())
    return s.strip('-') or 'subject'


def normalize_subject_key(text: Optional[str]) -> str:
    """Normalizes subject name/code to a clean lowercase alphanumeric string to prevent duplicate cards."""
    if not text:
        return ""
    return re.sub(r'[^a-z0-9]', '', text.lower())


def find_subject_definition(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    cleaned = raw.strip()
    norm = normalize_subject_key(cleaned)
    for subj in SUBJECT_DEFINITIONS:
        if norm == normalize_subject_key(subj["code"]):
            return subj
        if norm == normalize_subject_key(subj["id"]):
            return subj
        if norm == normalize_subject_key(subj["name"]):
            return subj
        for alias in subj.get("aliases", []):
            if norm == normalize_subject_key(alias):
                return subj
    return CODE_OR_SLUG_MAP.get(cleaned.upper()) or CODE_OR_SLUG_MAP.get(cleaned.lower())


def get_or_create_subject_definition(raw: str) -> Dict[str, Any]:
    """
    Returns standard subject definition if known, otherwise constructs a dynamic
    first-class subject definition with harmonious colors, slug, and code.
    Preserves user's actual subject name and code instead of creating arbitrary acronym collisions.
    """
    found = find_subject_definition(raw)
    if found:
        return found

    raw_clean = raw.strip()
    slug = slugify(raw_clean)

    # Extract sensible code and name (e.g. "BCS 301 - COA" -> code "BCS 301 - COA" or "BCS 301", name "COA")
    if " - " in raw_clean:
        parts = raw_clean.split(" - ", 1)
        code = parts[0].strip().upper()
        name = parts[1].strip()
    elif "-" in raw_clean and len(raw_clean.split("-")) == 2:
        parts = raw_clean.split("-", 1)
        code = parts[0].strip().upper()
        name = parts[1].strip()
    else:
        code = raw_clean.upper()
        name = raw_clean

    palette_idx = abs(hash(slug)) % len(PALETTE)
    color, bg = PALETTE[palette_idx]

    return {
        "id": slug,
        "name": name,
        "code": code,
        "aliases": [code, slug, raw_clean.upper(), raw_clean.lower(), normalize_subject_key(raw_clean)],
        "description": f"Curriculum modules, uploaded study materials, and assessments for {name}.",
        "color": color,
        "bg": bg,
        "chapters": []
    }


def matches_subject(raw_subject: Optional[str], subject_def: Dict[str, Any]) -> bool:
    """Checks whether a given subject code/id matches the subject definition using normalized keys."""
    if not raw_subject or not subject_def:
        return False
    cleaned = raw_subject.strip()
    norm_raw = normalize_subject_key(cleaned)
    if not norm_raw:
        return False

    if norm_raw == normalize_subject_key(subject_def.get("code")):
        return True
    if norm_raw == normalize_subject_key(subject_def.get("name")):
        return True
    if norm_raw == normalize_subject_key(subject_def.get("id")):
        return True
    for alias in subject_def.get("aliases", []):
        if norm_raw == normalize_subject_key(alias):
            return True
    return False


def get_active_subjects_for_user(db: Session, user_id: str) -> List[Dict[str, Any]]:
    """
    Returns the distinct list of subjects that the authenticated user actually owns
    STRICTLY from uploaded learning materials (materials_count > 0).
    A subject with 0 uploaded files is NEVER returned.
    """
    user_id_str = str(user_id)

    # STRICT RULE 1: Subjects ONLY originate from uploaded learning materials
    materials = db.query(LearningMaterial.subject_code).filter(
        LearningMaterial.user_id == user_id_str
    ).all()

    if not materials:
        return []

    seen_keys: Set[str] = set()
    definitions: List[Dict[str, Any]] = []

    for (m_code,) in materials:
        if not m_code or not m_code.strip():
            continue
        cleaned = m_code.strip()
        norm_key = normalize_subject_key(cleaned)
        if norm_key in seen_keys:
            continue
        seen_keys.add(norm_key)

        defn = get_or_create_subject_definition(cleaned)
        definitions.append(defn)

    return definitions


def compute_user_subject_progress(
    db: Session,
    user_id: str,
    subject_def: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Computes real progress, status, current topic, and chapter progression
    strictly based on the authenticated user's data in the database.
    
    Guarantees:
    - New subject with materials has 0% progress and 'Not Started' status.
    - Status: 0% = 'Not Started', 1-99% = 'In Progress', 100% = 'Completed'.
    - Current Topic: 'Not started yet' until the student begins studying.
    - Chapters are extracted and organized from user's uploaded materials for this subject.
    """
    user_id_str = str(user_id)

    # 1. Fetch user's uploaded materials for this subject
    user_materials = db.query(LearningMaterial).filter(
        LearningMaterial.user_id == user_id_str
    ).order_by(LearningMaterial.created_at.asc()).all()
    subject_materials = [
        m for m in user_materials if matches_subject(m.subject_code, subject_def)
    ]
    materials_count = len(subject_materials)

    # 2. Fetch user's study sessions and activity logs for reading tracking
    user_sessions = db.query(StudySession).filter(
        StudySession.user_id == user_id_str
    ).all()
    subject_sessions = [
        s for s in user_sessions if matches_subject(s.subject_id, subject_def)
    ]
    study_sessions_count = len(subject_sessions)

    # Activity logs for reading verification
    activity_logs = db.query(UserActivityLog).filter(
        UserActivityLog.user_id == user_id_str
    ).all()
    opened_material_titles: Set[str] = set()
    for log in activity_logs:
        if log.activity_type in ("material_opened", "topic_completed") and log.details:
            opened_material_titles.add(log.details.strip().lower())

    # 3. Fetch completed quiz attempts for this subject
    attempts_query = (
        db.query(QuizAttempt, Quiz)
        .join(Quiz, QuizAttempt.quiz_id == Quiz.id)
        .filter(
            QuizAttempt.user_id == user_id_str,
            QuizAttempt.status == "completed"
        )
        .all()
    )
    subject_attempts = [
        (att, q) for (att, q) in attempts_query if matches_subject(q.subject_code, subject_def)
    ]
    attempts_count = len(subject_attempts)

    # Explicit TopicCompletion records (manually marked or verified)
    explicit_topic_records = db.query(TopicCompletion).filter(
        TopicCompletion.user_id == user_id_str
    ).all()
    explicit_completed_topics: Set[str] = {
        et.topic_title.strip().lower() for et in explicit_topic_records
        if matches_subject(et.subject_code, subject_def)
    }

    # Pre-fetch question topic tags for quizzes in subject_attempts
    quiz_ids = list({q.id for att, q in subject_attempts})
    quiz_question_tags_map: Dict[int, List[str]] = {}
    if quiz_ids:
        all_qq = db.query(QuizQuestion.quiz_id, QuizQuestion.topic_tag).filter(
            QuizQuestion.quiz_id.in_(quiz_ids)
        ).all()
        for q_id, t_tag in all_qq:
            if q_id not in quiz_question_tags_map:
                quiz_question_tags_map[q_id] = []
            if t_tag and t_tag.strip():
                quiz_question_tags_map[q_id].append(t_tag.strip())

    # 4. Build dynamic chapters and subtopics using AI curriculum extractor
    from backend.app.services.curriculum_extractor import extract_curriculum_topics

    def topic_matches_quiz(topic_title: str, quiz_topic: Optional[str], question_tags: List[str]) -> bool:
        norm_t = re.sub(r'[^a-z0-9]', '', topic_title.lower())
        if not norm_t:
            return False
        # 1. Match quiz topic if specific
        if quiz_topic:
            norm_q = re.sub(r'[^a-z0-9]', '', quiz_topic.lower())
            if norm_q and (norm_q in norm_t or norm_t in norm_q):
                return True
        # 2. Match question topic tags
        for tag in question_tags:
            norm_tag = re.sub(r'[^a-z0-9]', '', tag.lower())
            if norm_tag and (norm_tag in norm_t or norm_t in norm_tag):
                return True
            t_words = {w for w in re.findall(r'[a-z]{4,}', topic_title.lower()) if w not in ("type", "types", "with", "from")}
            tag_words = {w for w in re.findall(r'[a-z]{4,}', tag.lower()) if w not in ("type", "types", "with", "from")}
            if t_words and tag_words and (t_words & tag_words):
                return True
        return False

    chapters_result = []
    all_evaluated_topics = []

    if subject_materials:
        chap_counter = 1
        for mat in subject_materials:
            mat_title = mat.title.strip() if mat.title else (mat.file_name or f"Material {mat.id}")
            curriculum = extract_curriculum_topics(
                db=db,
                material_id=mat.id,
                user_id=user_id_str,
                subject_code=subject_def["code"]
            )
            extracted_chaps = curriculum.get("chapters", [])

            for ch_data in extracted_chaps:
                chap_title = ch_data.get("title", f"Chapter {chap_counter} - {mat_title}").strip()
                raw_topics = ch_data.get("topics", [])
                topic_items = []

                for tp in raw_topics:
                    tp_title = tp.get("title", "").strip()
                    tp_summary = tp.get("summary", "").strip()
                    est_mins = int(tp.get("estimatedMinutes", 15))
                    norm_tp = tp_title.lower()

                    # Rule (a): Reading activity verified via activity log or study sessions
                    has_read = (
                        any(norm_tp in logged or logged in norm_tp for logged in opened_material_titles)
                        or any(mat_title.lower() in logged for logged in opened_material_titles)
                        or (mat.file_name and any(mat.file_name.lower() in logged for logged in opened_material_titles))
                        or study_sessions_count > 0
                    )

                    # Rule (b): Completed quiz attempts specifically matching this topic
                    matching_attempts = [
                        att for (att, q) in subject_attempts
                        if (q.material_id == mat.id) and topic_matches_quiz(tp_title, q.topic, quiz_question_tags_map.get(q.id, []))
                    ]
                    topic_attempts_count = len(matching_attempts)
                    scores = [a.score_percentage for a in matching_attempts if a.score_percentage is not None]
                    best_score = max(scores) if scores else None
                    avg_score = (sum(scores) / len(scores)) if scores else None

                    # Strict Topic Mastery Rule:
                    # Mastered ONLY IF: has_read == True AND >= 2 quiz attempts AND (best_score >= 70% or avg_score >= 70%)
                    is_manually_completed = (norm_tp in explicit_completed_topics)
                    passed_threshold = (best_score is not None and best_score >= 70.0) or (avg_score is not None and avg_score >= 70.0)

                    if (has_read and topic_attempts_count >= 2 and passed_threshold) or is_manually_completed:
                        t_status = "mastered"
                        t_label = "Mastered"
                        t_credit = 1.0
                        t_credit_pct = 100
                    elif topic_attempts_count >= 1:
                        t_status = "practised"
                        t_label = "Practised"
                        t_credit = 0.50
                        t_credit_pct = 50
                    elif has_read:
                        t_status = "reading"
                        t_label = "Reading"
                        t_credit = 0.25
                        t_credit_pct = 25
                    else:
                        t_status = "not_started"
                        t_label = "Not started"
                        t_credit = 0.0
                        t_credit_pct = 0

                    topic_obj = {
                        "id": len(all_evaluated_topics) + 1,
                        "title": tp_title,
                        "summary": tp_summary,
                        "estimated_minutes": est_mins,
                        "status": t_status,
                        "status_label": t_label,
                        "credit": t_credit,
                        "credit_percent": t_credit_pct,
                        "quiz_attempts_count": topic_attempts_count,
                        "best_score": best_score,
                        "has_read": has_read
                    }
                    topic_items.append(topic_obj)
                    all_evaluated_topics.append(topic_obj)

                # Determine Chapter Status and Duration from its topics
                chap_mins = sum(t["estimated_minutes"] for t in topic_items) or 20
                duration_str = f"{chap_mins} mins" if chap_mins < 60 else f"{chap_mins / 60:.1f} hrs"
                topics_in_chap = len(topic_items)
                mastered_in_chap = sum(1 for t in topic_items if t["status"] == "mastered")

                if topics_in_chap > 0 and mastered_in_chap == topics_in_chap:
                    chap_status = "completed"
                elif any(t["credit"] > 0 for t in topic_items):
                    chap_status = "current"
                else:
                    chap_status = "not_started"

                chapters_result.append({
                    "id": chap_counter,
                    "title": chap_title,
                    "status": chap_status,
                    "duration": duration_str,
                    "material_id": mat.id,
                    "topics_count": topics_in_chap,
                    "topics_mastered": mastered_in_chap,
                    "topics": topic_items
                })
                chap_counter += 1

    elif subject_def.get("chapters"):
        for ch_idx, ch in enumerate(subject_def["chapters"], 1):
            ch_title = ch["title"]
            norm_ch = ch_title.lower()
            is_done = norm_ch in explicit_completed_topics

            topic_obj = {
                "id": ch_idx,
                "title": ch_title,
                "summary": f"Curriculum module covering fundamental concepts of {ch_title}.",
                "estimated_minutes": 25,
                "status": "mastered" if is_done else "not_started",
                "status_label": "Mastered" if is_done else "Not started",
                "credit": 1.0 if is_done else 0.0,
                "credit_percent": 100 if is_done else 0,
                "quiz_attempts_count": 0,
                "best_score": None,
                "has_read": False
            }
            all_evaluated_topics.append(topic_obj)

            chapters_result.append({
                "id": ch["id"],
                "title": ch_title,
                "status": "completed" if is_done else "not_started",
                "duration": ch.get("duration", "45 mins"),
                "material_id": None,
                "topics_count": 1,
                "topics_mastered": 1 if is_done else 0,
                "topics": [topic_obj]
            })

    total_topics = max(1, len(all_evaluated_topics))
    topics_mastered = sum(1 for t in all_evaluated_topics if t["status"] == "mastered")
    topics_completed = topics_mastered
    total_credit_points = sum(t["credit"] for t in all_evaluated_topics)

    # 5. Authentic Progress Percentage: Average of all topic partial credits
    # Formula: sum(topic_credit) / total_topics * 100
    has_any_activity = (attempts_count > 0 or study_sessions_count > 0 or len(opened_material_titles) > 0)

    if all_evaluated_topics and total_credit_points > 0:
        raw_progress = round((total_credit_points / len(all_evaluated_topics)) * 100)
        # Strict rule: Cannot be 100% unless total topics >= 3 AND all topics are mastered
        if len(all_evaluated_topics) < 3 or topics_mastered < len(all_evaluated_topics):
            progress_percent = min(99, max(1, int(raw_progress)))
        else:
            progress_percent = 100
    else:
        progress_percent = 0

    # 6. Status determination:
    # 0% = "Not Started", 1-99% = "In Progress", 100% = "Completed"
    if progress_percent >= 100 and topics_mastered == len(all_evaluated_topics) and len(all_evaluated_topics) >= 3:
        status = "Completed"
        status_key = "completed"
    elif progress_percent > 0 or (has_any_activity and materials_count > 0):
        status = "In Progress"
        status_key = "in-progress"
    else:
        status = "Not Started"
        status_key = "not-started"

    # 7. Current Topic:
    # "Not started yet" if no activity, "All topics done" if completed, or next incomplete topic
    if not has_any_activity and progress_percent == 0:
        current_topic = "Not started yet"
    elif status == "Completed":
        current_topic = "All topics done"
    else:
        # Pick the next un-mastered topic
        next_incomplete = next((t["title"] for t in all_evaluated_topics if t["status"] != "mastered"), None)
        current_topic = next_incomplete or (all_evaluated_topics[0]["title"] if all_evaluated_topics else "Not started yet")

    last_activity_at: Optional[datetime] = None
    if subject_attempts:
        sorted_attempts = sorted(
            subject_attempts,
            key=lambda item: item[0].completed_at or item[0].started_at,
            reverse=True
        )
        last_activity_at = sorted_attempts[0][0].completed_at or sorted_attempts[0][0].started_at
    elif subject_sessions:
        sorted_sessions = sorted(
            subject_sessions,
            key=lambda s: s.ended_at or s.started_at,
            reverse=True
        )
        last_activity_at = sorted_sessions[0].ended_at or sorted_sessions[0].started_at
    elif subject_materials:
        latest_mat = sorted(subject_materials, key=lambda m: m.created_at, reverse=True)[0]
        last_activity_at = latest_mat.created_at

    # Update chapter statuses to reflect "current" topic if in-progress
    found_curr = False
    for ch in chapters_result:
        if ch["status"] == "completed":
            continue
        if status == "In Progress" and not found_curr:
            ch["status"] = "current"
            found_curr = True
            if current_topic == "Not started yet":
                current_topic = ch["title"]
        elif status == "Completed":
            ch["status"] = "completed"
        else:
            ch["status"] = "not_started"

    return {
        "id": subject_def["id"],
        "name": subject_def["name"],
        "code": subject_def["code"],
        "description": subject_def["description"],
        "color": subject_def["color"],
        "bg": subject_def["bg"],
        "status": status,
        "status_key": status_key,
        "progress_percent": progress_percent,
        "current_topic": current_topic,
        "materials_count": materials_count,
        "study_sessions_count": study_sessions_count,
        "quiz_attempts_count": attempts_count,
        "topics_completed": topics_completed,
        "total_topics": total_topics,
        "last_activity_at": last_activity_at.isoformat() if last_activity_at else None,
        "chapters": chapters_result
    }


def sync_subject_progress_record(
    db: Session,
    user_id: str,
    subject_def: Dict[str, Any],
    progress_data: Dict[str, Any]
) -> SubjectProgress:
    """
    Saves or updates the subject_progress record in SQLite for permanent persistence.
    """
    user_id_str = str(user_id)
    subject_code = subject_def["code"]

    rec = (
        db.query(SubjectProgress)
        .filter(
            SubjectProgress.user_id == user_id_str,
            SubjectProgress.subject_code == subject_code
        )
        .first()
    )

    last_act = None
    if progress_data.get("last_activity_at"):
        try:
            last_act = datetime.fromisoformat(progress_data["last_activity_at"])
        except Exception:
            last_act = None

    if not rec:
        rec = SubjectProgress(
            user_id=user_id_str,
            subject_code=subject_code,
            subject_slug=subject_def["id"],
            status=progress_data["status"],
            progress_percent=progress_data["progress_percent"],
            current_topic=progress_data["current_topic"],
            materials_count=progress_data["materials_count"],
            topics_completed=progress_data["topics_completed"],
            total_topics=progress_data["total_topics"],
            last_activity_at=last_act,
            updated_at=datetime.now(timezone.utc)
        )
        db.add(rec)
    else:
        rec.status = progress_data["status"]
        rec.progress_percent = progress_data["progress_percent"]
        rec.current_topic = progress_data["current_topic"]
        rec.materials_count = progress_data["materials_count"]
        rec.topics_completed = progress_data["topics_completed"]
        rec.total_topics = progress_data["total_topics"]
        rec.last_activity_at = last_act
        rec.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(rec)
    except Exception:
        db.rollback()

    return rec


def get_all_subjects_progress_for_user(
    db: Session,
    user_id: str
) -> List[Dict[str, Any]]:
    """
    Returns authentic progress for all subjects belonging to the authenticated user.
    If the user has not uploaded any materials or created any subjects, returns [].
    """
    active_subjects = get_active_subjects_for_user(db, user_id=user_id)
    if not active_subjects:
        return []

    results = []
    for subj in active_subjects:
        data = compute_user_subject_progress(db, user_id=user_id, subject_def=subj)
        sync_subject_progress_record(db, user_id=user_id, subject_def=subj, progress_data=data)
        results.append(data)
    return results


def update_subject_progress_for_event(
    db: Session,
    user_id: str,
    subject_code_or_slug: str
) -> Optional[Dict[str, Any]]:
    """
    Called whenever an event occurs (material upload, study session, quiz submission)
    to refresh the user's subject progress record immediately.
    """
    subj_def = get_or_create_subject_definition(subject_code_or_slug)
    data = compute_user_subject_progress(db, user_id=user_id, subject_def=subj_def)
    sync_subject_progress_record(db, user_id=user_id, subject_def=subj_def, progress_data=data)
    return data
