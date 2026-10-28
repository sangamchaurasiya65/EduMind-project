import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.database import init_db, SessionLocal
from backend.app.models.user import User


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    init_db()


import uuid


def register_and_login(client, prefix: str = "student", name: str = "Test Student") -> dict:
    clean_prefix = prefix.split("@")[0]
    unique_email = f"{clean_prefix}_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = client.post(
        "/api/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "confirm_password": "password123",
            "full_name": name
        }
    )
    assert reg_res.status_code == 201, f"Registration failed: {reg_res.text}"
    login_res = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": "password123"}
    )
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_new_user_subjects_progress():
    """
    Verifies that a brand-new user with no materials sees an empty subject list (len == 0).
    No hardcoded dummy subjects should appear for fresh users.
    """
    with TestClient(app) as client:
        headers = register_and_login(client, "brand_new_student_test@example.com", "Fresh Student")

        # Query subject progress
        res = client.get("/api/subjects/progress", headers=headers)
        assert res.status_code == 200
        subjects = res.json()

        # Zero dummy subjects for a new user
        assert len(subjects) == 0


def test_upload_material_creates_subject_with_not_started():
    """
    Verifies that uploading a material creates that subject card with:
    - materials_count == 1
    - status == 'Not Started'
    - progress_percent == 0
    - current_topic == 'Not started yet'
    - no other subjects are created
    """
    with TestClient(app) as client:
        headers = register_and_login(client, "upload_student_test@example.com", "Upload Student")

        # Upload a document to CS301 (Data Structures)
        doc_text = "Data Structures lecture note covering arrays, linked lists, stacks, and binary trees in full detail."
        upload_res = client.post(
            "/api/materials/upload",
            headers=headers,
            files={"file": ("ds_notes.txt", doc_text.encode("utf-8"), "text/plain")},
            data={"title": "Data Structures Primer", "subject_code": "CS301"}
        )
        assert upload_res.status_code == 201

        # Check progress
        res = client.get("/api/subjects/progress", headers=headers)
        assert res.status_code == 200
        subjects = res.json()

        assert len(subjects) == 1
        cs301 = subjects[0]
        assert cs301["code"] == "CS301"
        assert cs301["status"] == "Not Started"
        assert cs301["status_key"] == "not-started"
        assert cs301["materials_count"] == 1
        assert cs301["progress_percent"] == 0
        assert cs301["current_topic"] == "Not started yet"


def test_quiz_attempt_updates_progress_and_current_topic():
    """
    Verifies that completing a quiz for a subject advances status to 'In Progress',
    updates progress percent (> 0) and sets the real current topic.
    """
    with TestClient(app) as client:
        headers = register_and_login(client, "quiz_student_test@example.com", "Quiz Student")

        # Upload material 1
        doc_text = "Database Management relational models, SQL basics, select queries, joins, and database normalization forms."
        mat_res = client.post(
            "/api/materials/upload",
            headers=headers,
            files={"file": ("db_notes.txt", doc_text.encode("utf-8"), "text/plain")},
            data={"title": "SQL Basics Notes", "subject_code": "CS303"}
        )
        assert mat_res.status_code == 201
        mat_id = mat_res.json()["id"]

        # Upload material 2 (so total topics = 2, giving 50% progress upon 1 completed quiz)
        client.post(
            "/api/materials/upload",
            headers=headers,
            files={"file": ("er_notes.txt", "ER diagrams and entity relationship concepts.".encode("utf-8"), "text/plain")},
            data={"title": "Entity Relationship Modeling", "subject_code": "CS303"}
        )

        # Generate Quiz for SQL Basics
        gen_res = client.post(
            "/api/quizzes/generate",
            headers=headers,
            json={
                "material_id": mat_id,
                "title": "SQL Basics Assessment",
                "topic": "SQL Basics",
                "num_questions": 4,
                "difficulty": "Medium"
            }
        )
        assert gen_res.status_code == 201
        quiz_id = gen_res.json()["id"]

        # Start attempt
        start_res = client.post(f"/api/quizzes/{quiz_id}/attempts", headers=headers)
        assert start_res.status_code == 201
        attempt_id = start_res.json()["attempt_id"]
        questions = start_res.json()["questions"]
        assert len(questions) == 4

        # Submit attempt answering all 4 questions
        responses = [{"question_id": q["id"], "selected_index": 0} for q in questions]
        sub_res = client.post(
            f"/api/attempts/{attempt_id}/submit",
            headers=headers,
            json={"responses": responses, "time_taken_seconds": 60}
        )
        assert sub_res.status_code == 200

        # Query subject progress
        res = client.get("/api/subjects/progress", headers=headers)
        assert res.status_code == 200
        subjects = res.json()

        cs303 = next(s for s in subjects if s["code"] == "CS303")
        assert cs303["status"] == "In Progress"
        assert cs303["current_topic"] == "SQL Basics"
        assert cs303["topics_completed"] == 1
        assert cs303["total_topics"] == 2
        assert cs303["progress_percent"] == 50
        assert cs303["quiz_attempts_count"] == 1

        # Check detail endpoint
        detail_res = client.get(f"/api/subjects/{cs303['id']}/progress", headers=headers)
        assert detail_res.status_code == 200
        detail_data = detail_res.json()
        assert detail_data["code"] == "CS303"
        assert detail_data["current_topic"] == "SQL Basics"
        assert len(detail_data["chapters"]) >= 1
        assert detail_data["chapters"][0]["status"] == "completed"
