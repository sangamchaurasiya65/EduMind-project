import json
import uuid
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.config import settings
from backend.app.database import init_db


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    init_db()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_chat_unauthenticated_rejected(client):
    """
    Test 1:
    Calls to /api/chat without authentication must be rejected with 401.
    """
    res = client.post("/api/chat", json={"message": "explain binary search"})
    assert res.status_code == 401

    res_hist = client.get("/api/chat/history")
    assert res_hist.status_code == 401

    res_del = client.delete("/api/chat/history")
    assert res_del.status_code == 401


def test_chat_missing_key_returns_friendly_message(client):
    """
    Test 2:
    When GEMINI_API_KEY is not set or placeholder, app must not crash.
    It returns friendly message: "AI abhi setup nahi hai, .env mein GEMINI_API_KEY daalo."
    """
    uid = uuid.uuid4().hex[:8]
    email = f"chat_{uid}@college.edu"

    # Register & Login
    client.post("/api/auth/register", json={
        "full_name": "Chat Learner",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    token = client.post("/api/auth/login", json={"email": email, "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Ensure placeholder key
    with patch.object(settings, "GEMINI_API_KEY", "your_key_here"):
        res = client.post(
            "/api/chat",
            json={"message": "explain binary search"},
            headers=headers
        )
        assert res.status_code == 200
        content = res.text
        assert "AI abhi setup nahi hai, .env mein GEMINI_API_KEY daalo." in content


def test_chat_character_limit(client):
    """
    Test 3:
    Input messages exceeding 4000 characters must be rejected.
    """
    uid = uuid.uuid4().hex[:8]
    email = f"limit_{uid}@college.edu"

    client.post("/api/auth/register", json={
        "full_name": "Limit Tester",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    token = client.post("/api/auth/login", json={"email": email, "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    long_message = "a" * 4001
    res = client.post("/api/chat", json={"message": long_message}, headers=headers)
    assert res.status_code in (400, 422)


def test_chat_history_isolation_and_clear(client):
    """
    Test 4:
    Multi-tenant isolation: User A's chat history is not visible to User B.
    Clearing chat deletes only the requesting user's records.
    """
    uid_a = uuid.uuid4().hex[:8]
    email_a = f"usera_{uid_a}@college.edu"
    client.post("/api/auth/register", json={
        "full_name": "User Alpha",
        "email": email_a,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    token_a = client.post("/api/auth/login", json={"email": email_a, "password": "Password123!"}).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    uid_b = uuid.uuid4().hex[:8]
    email_b = f"userb_{uid_b}@college.edu"
    client.post("/api/auth/register", json={
        "full_name": "User Beta",
        "email": email_b,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    token_b = client.post("/api/auth/login", json={"email": email_b, "password": "Password123!"}).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A sends a message
    with patch.object(settings, "GEMINI_API_KEY", "your_key_here"):
        client.post("/api/chat", json={"message": "Alpha secret query"}, headers=headers_a)

    # Check User A history has messages
    hist_a = client.get("/api/chat/history", headers=headers_a).json()
    assert len(hist_a["messages"]) >= 1
    assert any("Alpha secret query" in m["content"] for m in hist_a["messages"])

    # User B history MUST be 0
    hist_b = client.get("/api/chat/history", headers=headers_b).json()
    assert len(hist_b["messages"]) == 0

    # User A clears chat
    del_res = client.delete("/api/chat/history", headers=headers_a).json()
    assert del_res["success"] is True

    # User A history is now 0
    hist_a_after = client.get("/api/chat/history", headers=headers_a).json()
    assert len(hist_a_after["messages"]) == 0


def test_chat_mocked_gemini_streaming_and_persistence(client):
    """
    Test 5:
    Simulates Google Gemini streaming response via google-genai Client mock:
    - Streams chunk-by-chunk in SSE format
    - Persists user question and complete AI answer in database
    """
    uid = uuid.uuid4().hex[:8]
    email = f"gemini_{uid}@college.edu"
    client.post("/api/auth/register", json={
        "full_name": "Gemini Student",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    token = client.post("/api/auth/login", json={"email": email, "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create mock response chunks
    chunk1 = MagicMock()
    chunk1.text = "Binary Search is a divide-and-conquer algorithm. "
    chunk2 = MagicMock()
    chunk2.text = "It operates in O(log n) time complexity."

    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content_stream.return_value = [chunk1, chunk2]

    with patch.object(settings, "GEMINI_API_KEY", "AIzaSyTestValidFakeKey123"), \
         patch("google.genai.Client", return_value=mock_client_instance):

        res = client.post(
            "/api/chat",
            json={
                "message": "explain binary search",
                "subject_code": "CS301",
                "subject_name": "Data Structures",
                "topic": "Binary Search Trees",
                "history": [{"role": "user", "content": "hello"}, {"role": "model", "content": "hi"}]
            },
            headers=headers
        )
        assert res.status_code == 200
        text = res.text
        assert "Binary Search is a divide-and-conquer algorithm." in text
        assert "O(log n)" in text
        assert "[DONE]" in text

    # Verify both User query and AI response are persisted in database
    hist = client.get("/api/chat/history", headers=headers).json()
    contents = [m["content"] for m in hist["messages"]]
    assert any("explain binary search" in c for c in contents)
    assert any("Binary Search is a divide-and-conquer algorithm." in c for c in contents)
