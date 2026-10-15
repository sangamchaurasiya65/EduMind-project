from typing import Generator, Tuple, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.config import settings

# Engine configuration (check_same_thread=False is required for SQLite with multi-threaded FastAPI)
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to provide a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> Tuple[bool, str, Dict[str, Any]]:
    """
    Actively checks the database connection by executing a test query.
    Returns (is_connected, status_message, metadata).
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar()
            if result == 1:
                return (
                    True,
                    "Database operational and accepting queries.",
                    {
                        "engine": "sqlite" if "sqlite" in settings.DATABASE_URL else "relational",
                        "status": "connected"
                    }
                )
            return (
                False,
                "Database query returned unexpected result.",
                {"status": "degraded"}
            )
    except Exception as exc:
        return (
            False,
            f"Database connection error: {str(exc)}",
            {"status": "disconnected", "error": str(exc)}
        )


def init_db() -> None:
    """
    Initializes database schema by registering all models and creating tables.
    Also handles safe column additions for existing SQLite tables.
    """
    # Import all models to register with Base metadata
    import backend.app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Safely migrate new columns if learning_materials already existed
    try:
        with engine.connect() as conn:
            cursor = conn.connection.cursor()
            cursor.execute("PRAGMA table_info(learning_materials)")
            existing_cols = {row[1] for row in cursor.fetchall()}
            if existing_cols:
                if "user_id" not in existing_cols:
                    cursor.execute("ALTER TABLE learning_materials ADD COLUMN user_id VARCHAR(100) DEFAULT 'student_default'")
                if "storage_path" not in existing_cols:
                    cursor.execute("ALTER TABLE learning_materials ADD COLUMN storage_path VARCHAR(500)")
                if "extracted_char_count" not in existing_cols:
                    cursor.execute("ALTER TABLE learning_materials ADD COLUMN extracted_char_count INTEGER DEFAULT 0")
                if "error_message" not in existing_cols:
                    cursor.execute("ALTER TABLE learning_materials ADD COLUMN error_message TEXT")
                conn.connection.commit()

            cursor.execute("PRAGMA table_info(quizzes)")
            existing_quiz_cols = {row[1] for row in cursor.fetchall()}
            if existing_quiz_cols:
                if "user_id" not in existing_quiz_cols:
                    cursor.execute("ALTER TABLE quizzes ADD COLUMN user_id VARCHAR(100) DEFAULT 'student_default'")
                if "generation_mode" not in existing_quiz_cols:
                    cursor.execute("ALTER TABLE quizzes ADD COLUMN generation_mode VARCHAR(50) DEFAULT 'fallback'")
                conn.connection.commit()

            cursor.execute("PRAGMA table_info(quiz_attempts)")
            existing_attempt_cols = {row[1] for row in cursor.fetchall()}
            if existing_attempt_cols:
                if "status" not in existing_attempt_cols:
                    cursor.execute("ALTER TABLE quiz_attempts ADD COLUMN status VARCHAR(50) DEFAULT 'in_progress'")
                if "unanswered_count" not in existing_attempt_cols:
                    cursor.execute("ALTER TABLE quiz_attempts ADD COLUMN unanswered_count INTEGER DEFAULT 0")
                conn.connection.commit()

            # Safely migrate users table columns if not present
            cursor.execute("PRAGMA table_info(users)")
            existing_user_cols = {row[1] for row in cursor.fetchall()}
            if existing_user_cols:
                if "course" not in existing_user_cols:
                    cursor.execute("ALTER TABLE users ADD COLUMN course VARCHAR(100)")
                if "semester" not in existing_user_cols:
                    cursor.execute("ALTER TABLE users ADD COLUMN semester VARCHAR(100)")
                if "role" not in existing_user_cols:
                    cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(100) DEFAULT 'Student'")
                if "learning_style" not in existing_user_cols:
                    cursor.execute("ALTER TABLE users ADD COLUMN learning_style VARCHAR(100)")
                if "daily_goal" not in existing_user_cols:
                    cursor.execute("ALTER TABLE users ADD COLUMN daily_goal VARCHAR(100)")
                if "preferred_subject" not in existing_user_cols:
                    cursor.execute("ALTER TABLE users ADD COLUMN preferred_subject VARCHAR(100)")
                conn.connection.commit()

            # Ensure user_activity_logs table exists with proper indexes
            cursor.execute("PRAGMA table_info(user_activity_logs)")
            if not cursor.fetchall():
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_activity_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id VARCHAR(100) NOT NULL,
                        activity_type VARCHAR(50) NOT NULL,
                        activity_date VARCHAR(10) NOT NULL,
                        details VARCHAR(255),
                        created_at DATETIME NOT NULL
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS ix_user_activity_logs_user_id ON user_activity_logs(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS ix_user_activity_logs_activity_date ON user_activity_logs(activity_date)")
                conn.connection.commit()

            # Ensure topic_completions table exists with proper indexes
            cursor.execute("PRAGMA table_info(topic_completions)")
            if not cursor.fetchall():
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS topic_completions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id VARCHAR(100) NOT NULL,
                        subject_code VARCHAR(50) NOT NULL,
                        topic_title VARCHAR(255) NOT NULL,
                        completed_at DATETIME NOT NULL
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS ix_topic_completions_user_id ON topic_completions(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS ix_topic_completions_subject_code ON topic_completions(subject_code)")
                cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_user_topic_completion ON topic_completions(user_id, subject_code, topic_title)")
                conn.connection.commit()

            # Ensure study_sessions table exists with proper indexes
            cursor.execute("PRAGMA table_info(study_sessions)")
            if not cursor.fetchall():
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS study_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id VARCHAR(100) NOT NULL,
                        subject_id VARCHAR(100),
                        started_at DATETIME NOT NULL,
                        ended_at DATETIME,
                        duration_seconds INTEGER NOT NULL DEFAULT 0
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS ix_study_sessions_user_id ON study_sessions(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS ix_study_sessions_subject_id ON study_sessions(subject_id)")
                conn.connection.commit()

            # Ensure subject_progress table exists with proper indexes
            cursor.execute("PRAGMA table_info(subject_progress)")
            if not cursor.fetchall():
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS subject_progress (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id VARCHAR(100) NOT NULL,
                        subject_code VARCHAR(50) NOT NULL,
                        subject_slug VARCHAR(100) NOT NULL,
                        status VARCHAR(50) NOT NULL DEFAULT 'Not Started',
                        progress_percent INTEGER NOT NULL DEFAULT 0,
                        current_topic VARCHAR(255) NOT NULL DEFAULT '—',
                        materials_count INTEGER NOT NULL DEFAULT 0,
                        topics_completed INTEGER NOT NULL DEFAULT 0,
                        total_topics INTEGER NOT NULL DEFAULT 6,
                        last_activity_at DATETIME,
                        updated_at DATETIME NOT NULL
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS ix_subject_progress_user_id ON subject_progress(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS ix_subject_progress_subject_code ON subject_progress(subject_code)")
                cursor.execute("CREATE INDEX IF NOT EXISTS ix_subject_progress_subject_slug ON subject_progress(subject_slug)")
                cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_user_subject_progress ON subject_progress(user_id, subject_code)")
                conn.connection.commit()
    except Exception:
        # Pass if table not created yet or already updated
        pass


    # Ensure demo user exists for seamless presentation and testing
    try:
        from backend.app.services.auth_service import hash_password
        from backend.app.models.user import User
        with SessionLocal() as db:
            demo_user = db.query(User).filter(User.email == "alex@example.com").first()
            if not demo_user:
                demo_user = User(
                    email="alex@example.com",
                    full_name="Alex",
                    hashed_password=hash_password("student123"),
                    is_active=True
                )
                db.add(demo_user)
                db.commit()
    except Exception:
        pass

