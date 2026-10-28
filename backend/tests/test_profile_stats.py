import uuid
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_new_user_stats_and_profile_not_set(client):
    """
    Test 1:
    A brand new account with no course/semester provided at signup
    must show:
    - Topics Completed: 0, subtext: "No subjects yet"
    - Quizzes Completed: 0, average_score: None, subtext: "No quizzes taken yet"
    - Study Streak: 0, longest: 0, "No streak yet", no personal best
    - course: None, semester: None, is_course_set: False, is_semester_set: False
    - Learning preferences: empty strings
    """
    uid = uuid.uuid4().hex[:8]
    email = f"fresh_{uid}@college.edu"

    # Register without course/semester
    reg_res = client.post("/api/auth/register", json={
        "full_name": "Fresh Student",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    assert reg_res.status_code == 201

    # Login
    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch profile
    prof_res = client.get("/api/profile", headers=headers)
    assert prof_res.status_code == 200
    data = prof_res.json()

    prof = data["profile"]
    stats = data["stats"]
    prefs = data["learning_preferences"]

    assert prof["name"] == "Fresh Student"
    assert prof["email"] == email
    assert prof["course"] is None
    assert prof["semester"] is None
    assert prof["is_course_set"] is False
    assert prof["is_semester_set"] is False

    assert stats["topics_completed"] == 0
    assert stats["topics_subtext"] == "No subjects yet"
    assert stats["quizzes_completed"] == 0
    assert stats["average_score"] is None
    assert stats["quizzes_subtext"] == "No quizzes taken yet"
    assert stats["current_streak"] == 0
    assert stats["longest_streak"] == 0
    assert stats["streak_subtext"] == "No streak yet"
    assert stats["has_personal_best"] is False

    assert prefs["learning_style"] == ""
    assert prefs["daily_goal"] == ""
    assert prefs["preferred_subject"] == ""


def test_edit_profile_and_learning_preferences_persistence(client):
    """
    Test 2:
    Updating profile info and preferences persists to the database
    and survives re-fetching / re-login.
    """
    uid = uuid.uuid4().hex[:8]
    email = f"persisted_{uid}@college.edu"

    # Register
    client.post("/api/auth/register", json={
        "full_name": "Before Edit",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })

    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Update profile
    up_res = client.put("/api/profile", json={
        "full_name": "After Edit",
        "course": "B.Tech CSE",
        "semester": "6th Semester"
    }, headers=headers)
    assert up_res.status_code == 200
    prof = up_res.json()["profile"]
    assert prof["name"] == "After Edit"
    assert prof["course"] == "B.Tech CSE"
    assert prof["semester"] == "6th Semester"
    assert prof["is_course_set"] is True
    assert prof["is_semester_set"] is True

    # Update learning preferences
    pref_res = client.put("/api/profile/preferences", json={
        "learning_style": "Problem-solving",
        "daily_goal": "2 hours",
        "preferred_subject": "Data Structures"
    }, headers=headers)
    assert pref_res.status_code == 200
    prefs = pref_res.json()["learning_preferences"]
    assert prefs["learning_style"] == "Problem-solving"
    assert prefs["daily_goal"] == "2 hours"
    assert prefs["preferred_subject"] == "Data Structures"

    # Simulate logout and re-login
    client.post("/api/auth/logout", headers=headers)
    relogin = client.post("/api/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    new_token = relogin.json()["access_token"]
    new_headers = {"Authorization": f"Bearer {new_token}"}

    fetched = client.get("/api/profile", headers=new_headers).json()
    assert fetched["profile"]["name"] == "After Edit"
    assert fetched["profile"]["course"] == "B.Tech CSE"
    assert fetched["profile"]["semester"] == "6th Semester"
    assert fetched["learning_preferences"]["learning_style"] == "Problem-solving"
    assert fetched["learning_preferences"]["daily_goal"] == "2 hours"


def test_activity_updates_streak_and_stats(client):
    """
    Test 3:
    Upload a material, complete a topic, take a quiz ->
    verify topics completed count increases, quizzes completed count increases,
    avg score is calculated accurately, and study streak is >= 1 Day.
    """
    uid = uuid.uuid4().hex[:8]
    email = f"active_{uid}@college.edu"

    client.post("/api/auth/register", json={
        "full_name": "Active Learner",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    token = client.post("/api/auth/login", json={
        "email": email,
        "password": "Password123!"
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Upload study material
    file_content = b"Binary Search Trees are node-based binary tree data structures which have properties: left subtree has keys lesser, right has keys greater."
    upload_res = client.post(
        "/api/materials/upload",
        files={"file": ("dsa_trees.txt", file_content, "text/plain")},
        data={"title": "Binary Search Trees", "subject_code": "CS301"},
        headers=headers
    )
    assert upload_res.status_code == 201

    # 2. Complete a topic
    top_res = client.post(
        "/api/subjects/data-structures/topics/toggle",
        json={"topic_title": "Binary Search Trees", "completed": True},
        headers=headers
    )
    assert top_res.status_code == 200
    assert top_res.json()["is_completed"] is True

    # Check stats after topic completion
    prof_after_top = client.get("/api/profile", headers=headers).json()
    stats1 = prof_after_top["stats"]
    assert stats1["topics_completed"] == 1
    assert stats1["topics_subtext"] == "Across 1 subject"
    assert stats1["current_streak"] == 1
    assert stats1["longest_streak"] >= 1
    assert stats1["has_personal_best"] is True

    # 3. Create and take a quiz
    gen_quiz = client.post(
        "/api/quizzes/generate",
        json={
            "material_id": upload_res.json()["id"],
            "title": "Trees Practice Quiz",
            "topic": "Binary Search Trees",
            "num_questions": 3,
            "difficulty": "Intermediate"
        },
        headers=headers
    )
    assert gen_quiz.status_code == 201
    quiz_id = gen_quiz.json()["id"]

    # Start attempt
    start_att = client.post(f"/api/quizzes/{quiz_id}/attempts", headers=headers)
    assert start_att.status_code == 201
    attempt_id = start_att.json()["attempt_id"]
    questions = start_att.json()["questions"]

    # Submit answers (select 0 for all questions)
    responses = [{"question_id": q["id"], "selected_index": 0} for q in questions]
    sub_res = client.post(
        f"/api/attempts/{attempt_id}/submit",
        json={"responses": responses, "time_taken_seconds": 45},
        headers=headers
    )
    assert sub_res.status_code == 200
    score_pct = sub_res.json()["score_percentage"]

    # 4. Check profile stats again
    prof_after_quiz = client.get("/api/profile", headers=headers).json()
    stats2 = prof_after_quiz["stats"]

    assert stats2["topics_completed"] >= 1
    assert stats2["quizzes_completed"] == 1
    assert stats2["average_score"] == int(round(score_pct))
    assert stats2["quizzes_subtext"] == f"Avg. score: {int(round(score_pct))}%"
    assert stats2["current_streak"] == 1


def test_user_data_isolation(client):
    """
    Test 4:
    Verify that User A's stats and preferences are completely isolated
    from User B's stats and preferences.
    """
    uid_a = uuid.uuid4().hex[:8]
    email_a = f"user_a_{uid_a}@college.edu"
    client.post("/api/auth/register", json={
        "full_name": "User Alpha",
        "email": email_a,
        "password": "Password123!",
        "confirm_password": "Password123!",
        "course": "B.Tech CSE",
        "semester": "6th Semester"
    })
    token_a = client.post("/api/auth/login", json={"email": email_a, "password": "Password123!"}).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    uid_b = uuid.uuid4().hex[:8]
    email_b = f"user_b_{uid_b}@college.edu"
    client.post("/api/auth/register", json={
        "full_name": "User Beta",
        "email": email_b,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    token_b = client.post("/api/auth/login", json={"email": email_b, "password": "Password123!"}).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A completes a topic
    client.post(
        "/api/subjects/data-structures/topics/toggle",
        json={"topic_title": "Linked Lists", "completed": True},
        headers=headers_a
    )

    # User A has 1 topic completed
    prof_a = client.get("/api/profile", headers=headers_a).json()
    assert prof_a["stats"]["topics_completed"] >= 1
    assert prof_a["profile"]["course"] == "B.Tech CSE"

    # User B MUST still have 0 topics completed, course None
    prof_b = client.get("/api/profile", headers=headers_b).json()
    assert prof_b["stats"]["topics_completed"] == 0
    assert prof_b["stats"]["topics_subtext"] == "No subjects yet"
    assert prof_b["stats"]["quizzes_completed"] == 0
    assert prof_b["stats"]["current_streak"] == 0
    assert prof_b["profile"]["course"] is None
    assert prof_b["profile"]["is_course_set"] is False
