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


def find_subject_definition(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    cleaned = raw.strip()
    return CODE_OR_SLUG_MAP.get(cleaned.upper()) or CODE_OR_SLUG_MAP.get(cleaned.lower())


def get_or_create_subject_definition(raw: str) -> Dict[str, Any]:
    """
    Returns standard subject definition if known, otherwise constructs a dynamic
    first-class subject definition with harmonious colors, slug, and code.
    """
    found = find_subject_definition(raw)
    if found:
        return found

    slug = slugify(raw)
    name = raw.strip().title()
    # Pick stable color from palette using hash of slug
    palette_idx = abs(hash(slug)) % len(PALETTE)
    color, bg = PALETTE[palette_idx]

    # Generate uppercase code: e.g. "Machine Learning" -> "ML101"
    words = re.findall(r'[a-zA-Z0-9]+', raw)
    if len(words) == 1 and len(words[0]) <= 8:
        code = words[0].upper()
    elif len(words) >= 2:
        code = "".join(w[0].upper() for w in words[:4])
    else:
        code = slug[:6].upper()

    return {
        "id": slug,
        "name": name,
        "code": code,
        "aliases": [code, slug, raw.strip().upper(), raw.strip().lower()],
        "description": f"Curriculum modules, uploaded study materials, and assessments for {name}.",
        "color": color,
        "bg": bg,
        "chapters": []
    }


def matches_subject(raw_subject: Optional[str], subject_def: Dict[str, Any]) -> bool:
    """Checks whether a given subject code/id from a record matches the subject definition."""
    if not raw_subject:
        return False
    cleaned = raw_subject.strip()
    if cleaned.upper() == subject_def["code"].upper():
        return True
    if cleaned.lower() == subject_def["id"].lower():
        return True
    if slugify(cleaned) == subject_def["id"].lower():
        return True
    for alias in subject_def.get("aliases", []):
        if cleaned.upper() == alias.upper() or cleaned.lower() == alias.lower():
            return True
    return False


def get_active_subjects_for_user(db: Session, user_id: str) -> List[Dict[str, Any]]:
    """
    Returns the distinct list of subjects that the authenticated user actually owns
    (via uploaded materials, study sessions, quizzes, or existing progress records).
    Never fabricates default subjects for a user with zero data.
    """
    user_id_str = str(user_id)
    raw_subject_keys: Set[str] = set()

    # 1. From uploaded learning materials
    materials = db.query(LearningMaterial.subject_code).filter(
        LearningMaterial.user_id == user_id_str
    ).all()
    for (m_code,) in materials:
        if m_code and m_code.strip():
            raw_subject_keys.add(m_code.strip())

    # 2. From saved subject progress records
    progress_records = db.query(SubjectProgress.subject_code, SubjectProgress.subject_slug).filter(
        SubjectProgress.user_id == user_id_str
    ).all()
    for code, slug in progress_records:
        if code and code.strip():
            raw_subject_keys.add(code.strip())
        elif slug and slug.strip():
            raw_subject_keys.add(slug.strip())

    # 3. From study sessions
    sessions = db.query(StudySession.subject_id).filter(
        StudySession.user_id == user_id_str
    ).all()
    for (s_id,) in sessions:
        if s_id and s_id.strip():
            raw_subject_keys.add(s_id.strip())

    # 4. From quizzes
    quizzes = db.query(Quiz.subject_code).filter(
        Quiz.user_id == user_id_str
    ).all()
    for (q_code,) in quizzes:
        if q_code and q_code.strip():
            raw_subject_keys.add(q_code.strip())

    if not raw_subject_keys:
        return []

    # Map keys to distinct subject definitions
    definitions: Dict[str, Dict[str, Any]] = {}
    for raw in raw_subject_keys:
        defn = get_or_create_subject_definition(raw)
        definitions[defn["id"]] = defn

    return list(definitions.values())


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

    # 2. Fetch user's study sessions for this subject
    user_sessions = db.query(StudySession).filter(
        StudySession.user_id == user_id_str
    ).all()
    subject_sessions = [
        s for s in user_sessions if matches_subject(s.subject_id, subject_def)
    ]
    study_sessions_count = len(subject_sessions)

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

    # 4. Extract answered questions to determine completed topics
    responses_query = (
        db.query(LearnerResponse, QuizQuestion, Quiz)
        .join(QuizQuestion, LearnerResponse.question_id == QuizQuestion.id)
        .join(QuizAttempt, LearnerResponse.attempt_id == QuizAttempt.id)
        .join(Quiz, QuizAttempt.quiz_id == Quiz.id)
        .filter(
            QuizAttempt.user_id == user_id_str,
            QuizAttempt.status == "completed"
        )
        .all()
    )

    topic_eval_count: Dict[str, int] = {}
    for resp, question, quiz in responses_query:
        if not matches_subject(quiz.subject_code, subject_def):
            continue
        if resp.selected_index is not None:
            resolved_topic = (
                question.topic_tag.strip()
                if (question.topic_tag and question.topic_tag.strip())
                else (quiz.topic.strip() if (quiz.topic and quiz.topic.strip()) else "General")
            )
            topic_eval_count[resolved_topic] = topic_eval_count.get(resolved_topic, 0) + 1

    completed_topics_set: Set[str] = {
        topic for topic, cnt in topic_eval_count.items() if cnt >= 1
    }

    # Include explicit TopicCompletion records for this user and subject
    explicit_topic_records = db.query(TopicCompletion).filter(
        TopicCompletion.user_id == user_id_str
    ).all()
    for et in explicit_topic_records:
        if matches_subject(et.subject_code, subject_def):
            completed_topics_set.add(et.topic_title.strip())

    completed_material_ids: Set[int] = {
        q.material_id for att, q in subject_attempts if q.material_id is not None
    }

    # 5. Build dynamic chapters / topics for this subject
    # Chapters are organized from uploaded materials + template chapters
    chapters_result = []
    if subject_materials:
        # Each uploaded material forms a chapter in this subject
        for idx, mat in enumerate(subject_materials):
            mat_title = mat.title.strip() if mat.title else (mat.file_name or f"Chapter {idx + 1}")
            is_mat_done = (mat.id in completed_material_ids) or any(
                mat_title.lower().strip() == ct.lower().strip()
                for ct in completed_topics_set
            )
            # Duration based on extracted character count
            approx_mins = max(15, min(120, round(mat.extracted_char_count / 150))) if mat.extracted_char_count else 20
            duration_str = f"{approx_mins} mins" if approx_mins < 60 else f"{approx_mins / 60:.1f} hrs"

            chapters_result.append({
                "id": idx + 1,
                "title": mat_title,
                "status": "completed" if is_mat_done else "not_started",
                "duration": duration_str,
                "material_id": mat.id
            })
    elif subject_def.get("chapters"):
        # If no materials uploaded yet but template exists
        for ch in subject_def["chapters"]:
            ch_done = any(
                (ch["title"].lower() in ct.lower() or ct.lower() in ch["title"].lower())
                for ct in completed_topics_set
            )
            chapters_result.append({
                "id": ch["id"],
                "title": ch["title"],
                "status": "completed" if ch_done else "not_started",
                "duration": ch["duration"],
                "material_id": None
            })

    if subject_materials:
        total_topics = max(1, len(chapters_result))
        topics_completed = min(total_topics, sum(1 for ch in chapters_result if ch["status"] == "completed"))
    else:
        total_topics = max(1, len(chapters_result))
        topics_completed = min(total_topics, max(
            sum(1 for ch in chapters_result if ch["status"] == "completed"),
            len(completed_topics_set)
        ))

    # 6. Real Progress Percentage:
    # Rule: If user has not attempted any quizzes, study sessions, or completed topics, progress is 0%
    has_started_studying = (attempts_count > 0 or study_sessions_count > 0 or topics_completed > 0)

    if not has_started_studying:
        progress_percent = 0
    else:
        if topics_completed > 0:
            progress_percent = min(100, int((topics_completed / total_topics) * 100))
        else:
            # Active in quizzes or sessions but haven't fully cleared a topic threshold yet
            progress_percent = min(90, max(5, attempts_count * 10 + study_sessions_count * 5))

    # 7. Status determination:
    # 0% = "Not Started", 1-99% = "In Progress", 100% = "Completed"
    if progress_percent >= 100:
        status = "Completed"
        status_key = "completed"
    elif progress_percent > 0:
        status = "In Progress"
        status_key = "in-progress"
    else:
        status = "Not Started"
        status_key = "not-started"

    # 8. Current Topic:
    # "Not started yet" until student actually engages with a topic
    current_topic = "Not started yet"
    last_activity_at: Optional[datetime] = None

    if has_started_studying:
        # Pick latest attempt topic
        if subject_attempts:
            sorted_attempts = sorted(
                subject_attempts,
                key=lambda item: item[0].completed_at or item[0].started_at,
                reverse=True
            )
            latest_att, latest_quiz = sorted_attempts[0]
            last_activity_at = latest_att.completed_at or latest_att.started_at
            if latest_quiz.topic and latest_quiz.topic.strip():
                current_topic = latest_quiz.topic.strip()

        # Or pick latest study session
        if subject_sessions:
            sorted_sessions = sorted(
                subject_sessions,
                key=lambda s: s.ended_at or s.started_at,
                reverse=True
            )
            sess_time = sorted_sessions[0].ended_at or sorted_sessions[0].started_at
            if not last_activity_at or (sess_time and sess_time > last_activity_at):
                last_activity_at = sess_time
            if current_topic == "Not started yet" and chapters_result:
                current_topic = chapters_result[0]["title"]
    elif subject_materials:
        # Note uploaded recently, set last_activity_at to upload time
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
