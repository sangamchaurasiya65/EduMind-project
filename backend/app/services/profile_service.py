from datetime import datetime, timezone, timedelta, date
from typing import Dict, Any, List, Optional, Tuple, Set
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.user import User
from backend.app.models.activity_log import UserActivityLog
from backend.app.models.topic_completion import TopicCompletion
from backend.app.models.attempt import QuizAttempt, LearnerResponse
from backend.app.models.quiz import Quiz, QuizQuestion
from backend.app.models.material import LearningMaterial
from backend.app.models.study_session import StudySession


def log_user_activity(
    db: Session,
    user_id: str,
    activity_type: str,
    details: Optional[str] = None
) -> UserActivityLog:
    """
    Logs a study activity in the database for the given user with today's date.
    Activity types:
      - 'topic_completed': user finished/marked a chapter or topic
      - 'material_opened': user opened/reviewed/uploaded a document
      - 'quiz_submitted': user submitted a quiz assessment
      - 'study_session': user engaged in an active study session
    """
    user_id_str = str(user_id)
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    entry = UserActivityLog(
        user_id=user_id_str,
        activity_type=activity_type,
        activity_date=today_str,
        details=details[:250] if details else None
    )
    db.add(entry)
    try:
        db.commit()
        db.refresh(entry)
    except Exception:
        db.rollback()
    return entry


def get_user_study_dates(db: Session, user_id: str) -> List[date]:
    """
    Retrieves all distinct calendar dates on which the user engaged in study activity.
    Sources:
      1. UserActivityLog entries
      2. QuizAttempt (completed / started)
      3. LearningMaterial uploads
      4. StudySession records
    Guarantees that pre-existing authentic activities are seamlessly included.
    """
    user_id_str = str(user_id)
    distinct_dates: Set[date] = set()

    # 1. UserActivityLog
    logged_dates = db.query(UserActivityLog.activity_date).filter(
        UserActivityLog.user_id == user_id_str
    ).distinct().all()
    for (d_str,) in logged_dates:
        try:
            parsed = datetime.strptime(d_str, "%Y-%m-%d").date()
            distinct_dates.add(parsed)
        except Exception:
            pass

    # 2. Completed Quiz Attempts
    quiz_dates = db.query(QuizAttempt.completed_at, QuizAttempt.started_at).filter(
        QuizAttempt.user_id == user_id_str,
        QuizAttempt.status == "completed"
    ).all()
    for comp_at, start_at in quiz_dates:
        dt = comp_at or start_at
        if dt:
            distinct_dates.add(dt.date())

    # 3. Learning Materials
    material_dates = db.query(LearningMaterial.created_at).filter(
        LearningMaterial.user_id == user_id_str
    ).all()
    for (c_at,) in material_dates:
        if c_at:
            distinct_dates.add(c_at.date())

    # 4. Study Sessions
    session_dates = db.query(StudySession.started_at).filter(
        StudySession.user_id == user_id_str
    ).all()
    for (s_at,) in session_dates:
        if s_at:
            distinct_dates.add(s_at.date())

    return sorted(list(distinct_dates))


def calculate_study_streak(dates: List[date]) -> Tuple[int, int]:
    """
    Calculates current streak and longest streak from sorted unique activity dates.
    Streak Rules:
      - If user has no activity today and no activity yesterday, current streak = 0.
      - If user has activity today, streak counts backwards consecutive days starting today.
      - If user has no activity today, but has activity yesterday, streak counts backwards starting yesterday.
      - Longest streak is the maximum consecutive run of days across all history.
      - For a user with zero activity, both are 0.
    """
    if not dates:
        return 0, 0

    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    dates_set = set(dates)

    # 1. Current Streak
    current_streak = 0
    if today in dates_set:
        current_streak = 1
        check_day = today - timedelta(days=1)
        while check_day in dates_set:
            current_streak += 1
            check_day -= timedelta(days=1)
    elif yesterday in dates_set:
        current_streak = 1
        check_day = yesterday - timedelta(days=1)
        while check_day in dates_set:
            current_streak += 1
            check_day -= timedelta(days=1)
    else:
        current_streak = 0

    # 2. Longest Streak
    longest_streak = 0
    current_run = 0
    prev_date: Optional[date] = None

    for d in dates:
        if prev_date is None:
            current_run = 1
        elif d == prev_date + timedelta(days=1):
            current_run += 1
        elif d == prev_date:
            pass  # duplicate date
        else:
            current_run = 1
        prev_date = d
        if current_run > longest_streak:
            longest_streak = current_run

    return current_streak, longest_streak


def get_user_profile_data(db: Session, user: User) -> Dict[str, Any]:
    """
    Computes real, strictly authenticated profile info, preferences, and activity statistics:
    1. Topics Completed:
       - Unique topics completed by this user.
       - Count of subjects with at least 1 completed topic.
       - For new user: 0 and "No subjects yet".
    2. Quizzes Completed:
       - Count of completed quizzes by this user.
       - Real average score percentage (or None for new user).
       - For new user: 0 and "No quizzes taken yet".
    3. Study Streak:
       - Real consecutive days streak (0 Days for new user).
       - Longest streak (Personal best only shown if longest_streak > 0).
    4. Profile Info & Learning Preferences from database.
    """
    user_id_str = str(user.id)

    # -------------------------------------------------------------
    # 1. TOPICS COMPLETED
    # -------------------------------------------------------------
    # Distinct topics completed per subject
    subject_topics: Dict[str, Set[str]] = {}

    # A. Explicit Topic Completions
    completions = db.query(TopicCompletion).filter(
        TopicCompletion.user_id == user_id_str
    ).all()
    for comp in completions:
        s_code = comp.subject_code.strip().upper()
        if s_code not in subject_topics:
            subject_topics[s_code] = set()
        subject_topics[s_code].add(comp.topic_title.strip())

    # B. Topics derived from evaluated Quiz Responses for this user
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
    for resp, q, quiz in responses_query:
        if resp.selected_index is not None:
            s_code = (quiz.subject_code or "GENERAL").strip().upper()
            t_name = (
                q.topic_tag.strip()
                if (q.topic_tag and q.topic_tag.strip())
                else (quiz.topic.strip() if (quiz.topic and quiz.topic.strip()) else "General")
            )
            if s_code not in subject_topics:
                subject_topics[s_code] = set()
            subject_topics[s_code].add(t_name)

    # Calculate topics completed & subjects count
    total_topics_completed = sum(len(topics) for topics in subject_topics.values())
    subjects_with_topics = sum(1 for topics in subject_topics.values() if len(topics) >= 1)

    if total_topics_completed == 0 or subjects_with_topics == 0:
        topics_subtext = "No subjects yet"
    elif subjects_with_topics == 1:
        topics_subtext = "Across 1 subject"
    else:
        topics_subtext = f"Across {subjects_with_topics} subjects"

    # -------------------------------------------------------------
    # 2. QUIZZES COMPLETED & AVERAGE SCORE
    # -------------------------------------------------------------
    attempts = db.query(QuizAttempt).filter(
        QuizAttempt.user_id == user_id_str,
        QuizAttempt.status == "completed"
    ).all()
    quizzes_completed = len(attempts)

    if quizzes_completed == 0:
        avg_score = None
        quizzes_subtext = "No quizzes taken yet"
    else:
        avg_val = sum(a.score_percentage for a in attempts) / float(quizzes_completed)
        avg_score = int(round(avg_val))
        quizzes_subtext = f"Avg. score: {avg_score}%"

    # -------------------------------------------------------------
    # 3. STUDY STREAK
    # -------------------------------------------------------------
    dates = get_user_study_dates(db, user_id=user_id_str)
    current_streak, longest_streak = calculate_study_streak(dates)

    if longest_streak > 0:
        if current_streak == longest_streak and current_streak > 0:
            streak_subtext = "Personal best 🔥"
        else:
            streak_subtext = f"Personal best: {longest_streak} Days"
    else:
        streak_subtext = "No streak yet"

    # -------------------------------------------------------------
    # 4. PROFILE INFO & PREFERENCES
    # -------------------------------------------------------------
    course_display = user.course if (user.course and user.course.strip()) else None
    semester_display = user.semester if (user.semester and user.semester.strip()) else None
    role_display = user.role if (user.role and user.role.strip()) else ("Student" if not course_display else f"{course_display} Student")

    return {
        "profile": {
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "course": course_display,
            "semester": semester_display,
            "role": role_display,
            "is_course_set": bool(course_display),
            "is_semester_set": bool(semester_display)
        },
        "learning_preferences": {
            "learning_style": user.learning_style or "",
            "daily_goal": user.daily_goal or "",
            "preferred_subject": user.preferred_subject or ""
        },
        "stats": {
            "topics_completed": total_topics_completed,
            "topics_completed_subjects_count": subjects_with_topics,
            "topics_subtext": topics_subtext,
            "quizzes_completed": quizzes_completed,
            "average_score": avg_score,
            "quizzes_subtext": quizzes_subtext,
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "streak_subtext": streak_subtext,
            "has_personal_best": longest_streak > 0
        }
    }
