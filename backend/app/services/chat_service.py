import os
import time
import logging
from typing import List, Dict, Any, Generator, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models.material import LearningMaterial
from backend.app.models.chat_message import ChatMessage

logger = logging.getLogger("edumind.chat")

# System instruction strictly adhering to user's pedagogical requirements
BASE_SYSTEM_INSTRUCTION = """Tum EduMind AI ho, ek friendly aur samajhdaar study tutor, B.Tech/college students ke liye.
- Student jis bhasha mein poochhe (English, Hindi ya Hinglish), usi mein jawab do.
- Pehle concept simple shabdon mein samjhao, jaise dost ko samjha rahe ho. Zaroorat ho to detail do.
- Structure: (1) 1-2 line ki simple definition, (2) real-life ya chhota example, (3) steps ya key points, (4) coding topics mein clean code example comments ke saath, (5) relevant ho to time/space complexity ya formula.
- Jawab chhota aur clear rakho. Student 'detail mein' bole tabhi gehra jao.
- Har jawab ke end mein ek chhota follow-up suggest karo.
- Padhai se bahar ka sawal ho to bhi politely madad karo.
- Pakka jawab na pata ho to honestly bolo, galat ya banaya hua jawab mat do.
- Math aur code proper formatting mein likho."""

# In-memory per-user rate limiting (max 15 requests per 60 seconds)
_user_request_timestamps: Dict[str, List[float]] = {}
RATE_LIMIT_WINDOW_SECONDS = 60
MAX_REQUESTS_PER_WINDOW = 15


def check_user_rate_limit(user_id: str) -> Tuple[bool, Optional[str]]:
    """
    Ensures student does not exceed fair usage request frequency.
    """
    now = time.time()
    timestamps = _user_request_timestamps.get(user_id, [])
    
    # Filter out timestamps older than the window
    valid_timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW_SECONDS]
    
    if len(valid_timestamps) >= MAX_REQUESTS_PER_WINDOW:
        _user_request_timestamps[user_id] = valid_timestamps
        return False, "Rate limit reached. Please wait a few seconds before sending another question."
        
    valid_timestamps.append(now)
    _user_request_timestamps[user_id] = valid_timestamps
    return True, None


def extract_relevant_material_chunks(
    db: Session,
    user_id: str,
    query: str,
    subject_code: Optional[str] = None,
    max_chunks: int = 3
) -> List[Dict[str, str]]:
    """
    Searches user's uploaded documents for paragraphs matching the student's question.
    Only accesses documents belonging to the authenticated learner.
    """
    user_id_str = str(user_id)
    q = db.query(LearningMaterial).filter(
        LearningMaterial.user_id == user_id_str,
        LearningMaterial.status == "ready"
    )
    if subject_code:
        q = q.filter(LearningMaterial.subject_code == subject_code.strip())
        
    materials = q.order_by(LearningMaterial.created_at.desc()).limit(10).all()
    if not materials:
        # Fallback to any subject if filtered subject yielded no docs
        materials = db.query(LearningMaterial).filter(
            LearningMaterial.user_id == user_id_str,
            LearningMaterial.status == "ready"
        ).order_by(LearningMaterial.created_at.desc()).limit(10).all()
        
    if not materials:
        return []

    # Clean query keywords (ignore very short stop words)
    keywords = [w.lower() for w in query.split() if len(w) > 3]
    if not keywords:
        keywords = [w.lower() for w in query.split() if len(w) > 2]

    matched_chunks = []
    
    for mat in materials:
        if not mat.extracted_text:
            continue
            
        paragraphs = [p.strip() for p in mat.extracted_text.split("\n\n") if len(p.strip()) > 40]
        if not paragraphs:
            paragraphs = [p.strip() for p in mat.extracted_text.split("\n") if len(p.strip()) > 40]
            
        for p in paragraphs:
            p_lower = p.lower()
            score = sum(1 for kw in keywords if kw in p_lower)
            if score > 0:
                matched_chunks.append({
                    "title": mat.title,
                    "subject_code": mat.subject_code,
                    "text": p[:600],
                    "score": score
                })
                
    # Sort by keyword match score
    matched_chunks.sort(key=lambda x: x["score"], reverse=True)
    return matched_chunks[:max_chunks]


def build_system_instruction(
    subject_code: Optional[str] = None,
    subject_name: Optional[str] = None,
    topic: Optional[str] = None,
    material_chunks: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Constructs the prompt instructions including subject context and uploaded material context.
    """
    parts = [BASE_SYSTEM_INSTRUCTION]

    # Add subject and topic context if provided
    context_lines = []
    if subject_name or subject_code:
        subj_str = f"{subject_name} ({subject_code})" if subject_name and subject_code else (subject_name or subject_code)
        context_lines.append(f"Current Subject: {subj_str}")
    if topic:
        context_lines.append(f"Current Topic: {topic}")

    if context_lines:
        parts.append(
            "\n--- Current Study Context ---\n"
            + "\n".join(context_lines)
            + "\n(Note: Student ko kisi bhi subject ya topic ke sawal poochhne ki poori azaadi hai. Context sirf guidance ke liye hai.)"
        )

    # Add uploaded materials context
    if material_chunks and len(material_chunks) > 0:
        docs_text = []
        for i, chunk in enumerate(material_chunks, 1):
            docs_text.append(
                f"[{i}] Material: \"{chunk['title']}\" (Subject: {chunk['subject_code']})\n"
                f"{chunk['text']}"
            )
        parts.append(
            "\n--- Student's Uploaded Notes/Materials Context ---\n"
            + "\n\n".join(docs_text)
            + "\n----------------------------------------------------\n"
            + "RAG Instruction: Agar student ke sawal ka answer upar diye gaye Student's Uploaded Notes mein milta hai, to pehle usi material ke aadhar par jawab do aur mention karo ki kaunse material se answer liya gaya hai (jaise: 'Aapke uploaded notes [Title] ke anusaar...').\n"
            + "Agar student ke uploaded materials mein ye topic na ho, to apni general academic knowledge se best aur simple jawab do, aur politely bata do ki ye topic aapke notes mein nahi mila isliye general concept se explain kiya ja raha hai."
        )
    else:
        parts.append(
            "\n(Student ne abhi is topic par koi material upload nahi kiya hai. Apni general academic knowledge se standard friendly tutor bankar jawab do.)"
        )

    return "\n\n".join(parts)


def stream_gemini_chat_response(
    message: str,
    history: Optional[List[Dict[str, Any]]] = None,
    subject_code: Optional[str] = None,
    subject_name: Optional[str] = None,
    topic: Optional[str] = None,
    material_chunks: Optional[List[Dict[str, str]]] = None
) -> Generator[str, None, None]:
    """
    Generates word-by-word streaming responses via official Google Gen AI SDK (`google-genai`).
    Gracefully handles missing keys, invalid keys, rate limits, and network errors.
    """
    # Check settings first to respect test patches, otherwise fallback to env
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.lower() in ("your_key_here", "your_gemini_api_key_here", "your_api_key_here", "none", ""):
        api_key = settings.GEMINI_API_KEY.strip()
    else:
        # Dynamically reload environment variables from .env if present
        from dotenv import load_dotenv
        from backend.app.config import BASE_DIR
        env_file = BASE_DIR / ".env"
        if env_file.exists():
            load_dotenv(dotenv_path=env_file, override=True)
        api_key = (os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY or "").strip()

    # Check for placeholder or missing key
    is_missing_key = (
        not api_key
        or api_key.lower() in ("your_key_here", "your_gemini_api_key_here", "your_api_key_here", "none", "")
    )

    if is_missing_key:
        yield "AI abhi setup nahi hai, .env mein GEMINI_API_KEY daalo."
        return

    # Prepare Google GenAI Client and Models
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        logger.error("google-genai SDK is not installed in the active environment.")
        yield "AI service library setup incomplete. Please ensure google-genai is installed."
        return

    primary_model = (os.getenv("GEMINI_MODEL") or settings.GEMINI_MODEL or "gemini-3.5-flash-lite").strip()
    system_instruction = build_system_instruction(
        subject_code=subject_code,
        subject_name=subject_name,
        topic=topic,
        material_chunks=material_chunks
    )

    # Build multi-turn contents list (last 10-15 messages)
    contents: List[types.Content] = []
    
    if history and isinstance(history, list):
        # Slice last 14 messages so current message is 15th
        recent_history = history[-14:]
        for turn in recent_history:
            role_val = turn.get("role", "user")
            # Map frontend roles to Gemini roles ('user' or 'model')
            gemini_role = "model" if role_val in ("model", "ai", "assistant") else "user"
            content_text = str(turn.get("content") or turn.get("text") or "").strip()
            if content_text:
                contents.append(
                    types.Content(
                        role=gemini_role,
                        parts=[types.Part.from_text(text=content_text)]
                    )
                )

    # Add the current user query
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=message)]
        )
    )

    # Candidate models for resilience (in case of 404 retirement or 503 high-demand spike)
    candidate_models = [primary_model]
    for fallback in ["gemini-3.5-flash-lite", "gemini-3-flash-preview", "gemini-3.8-flash"]:
        if fallback not in candidate_models:
            candidate_models.append(fallback)

    client = genai.Client(api_key=api_key)
    last_error: Optional[Exception] = None
    stream_started = False

    for current_model in candidate_models:
        try:
            print(f"[CHAT API] Sending request to model: '{current_model}' (User query: {message[:50]}...)", flush=True)
            response_stream = client.models.generate_content_stream(
                model=current_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7
                )
            )

            has_output = False
            for chunk in response_stream:
                if chunk.text:
                    has_output = True
                    stream_started = True
                    yield chunk.text

            if has_output:
                print(f"[CHAT API] Successfully streamed response from '{current_model}'", flush=True)
                return

        except Exception as exc:
            last_error = exc
            print(f"[CHAT ERROR] Model '{current_model}' failed with {type(exc).__name__}: {exc}", flush=True)
            logger.error(f"Gemini API streaming error on model '{current_model}': {exc}", exc_info=True)
            if stream_started:
                # If stream already began sending chunks to client, don't attempt to append another model halfway
                break
            # Otherwise proceed to try next candidate model in list

    # If all candidate models failed to yield output
    err_str = str(last_error) if last_error else "No output generated"
    print(f"[CHAT ERROR FINAL] Generation failed. Error details: {err_str}", flush=True)

    if "API_KEY_INVALID" in err_str or "invalid api key" in err_str.lower() or "unregistered" in err_str.lower():
        yield "Aapki GEMINI_API_KEY galat ya expired hai. Kripya Google AI Studio se nayi key lekar backend/.env mein update karein."
    elif "429" in err_str or "quota" in err_str.lower() or "resourceexhausted" in err_str.lower():
        yield "Gemini API rate limit reach ho gayi hai. Kripya kuch second intezar karke dobara try karein."
    elif "503" in err_str or "high demand" in err_str.lower() or "unavailable" in err_str.lower():
        yield "Gemini servers par temporary high traffic hai. Kripya 5-10 second baad Retry par click karein."
    elif "404" in err_str or "not found" in err_str.lower() or "no longer available" in err_str.lower():
        yield f"Selected AI model available nahi hai. .env mein GEMINI_MODEL=gemini-3.5-flash-lite set karein."
    else:
        yield f"AI se connect karne mein samasya aayi ({type(last_error).__name__}). Kripya Retry button par click karein."

