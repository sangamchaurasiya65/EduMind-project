import json
import os
import random
import re
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

from dotenv import load_dotenv
from backend.app.config import BASE_DIR, settings

logger = logging.getLogger("edumind.quiz")

MIN_TEXT_LENGTH_FOR_QUIZ = 100


class QuizGenerationError(Exception):
    """Raised when quiz generation fails due to input validation or provider errors."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass
class GeneratedQuestion:
    question_text: str
    options: List[str]
    correct_index: int
    explanation: str
    topic_tag: str
    difficulty: str
    order_num: int


# ==============================================================================
# RIGOROUS QUESTION VALIDATION & SANITIZATION ENGINE
# ==============================================================================

FORBIDDEN_OPTION_PATTERNS = [
    r"\ball of the above\b",
    r"\bnone of the above\b",
    r"\bboth a and b\b",
    r"\bboth b and c\b",
    r"\bboth a and c\b",
    r"\ball of these\b",
    r"\bnone of these\b",
    r"\bneither a nor b\b"
]

STOPWORD_QUESTION_PATTERNS = [
    r"\b(definition|meaning|role|concept)\s+of\s+['\"]?(following|above|given|below|stated)['\"]?",
    r"^\s*which of the following\??\s*$",
    r"^\s*what is the role of following\??\s*$"
]


def clean_question_prefix(text: str) -> str:
    """Removes lazy prefixes like 'According to the learning material...'"""
    cleaned = re.sub(
        r"^(according to the (learning |study )?material,?\s*|based on the (provided )?material,?\s*|as per the document,?\s*)",
        "",
        text.strip(),
        flags=re.IGNORECASE
    )
    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned.strip()


def validate_and_sanitize_question(
    q_data: Dict[str, Any],
    default_topic: str,
    difficulty: str,
    order_num: int
) -> Tuple[Optional[GeneratedQuestion], Optional[str]]:
    """
    Validates a single question against strict academic quality rules:
    1. Question text is clean, self-contained, and >= 6 words.
    2. No meaningless stopword targets ('following', 'given', 'above').
    3. Exactly 4 unique, concise options.
    4. No forbidden meta-options ('All of the above', 'None of the above').
    5. Balanced option lengths: correct option length cannot exceed 1.8x the average
       distractor length (prevents dead giveaways).
    6. Shuffles options so correctIndex is randomly distributed across 0, 1, 2, 3.
    7. Provides a clear explanation.
    """
    if not isinstance(q_data, dict):
        return None, "Question payload is not a valid object."

    # 1. Validate Question Text
    raw_text = str(q_data.get("question") or q_data.get("question_text") or "").strip()
    clean_text = clean_question_prefix(raw_text)

    words = clean_text.split()
    if len(words) < 6:
        return None, f"Question is too short or incomplete ({len(words)} words found, minimum 6 required)."

    for pat in STOPWORD_QUESTION_PATTERNS:
        if re.search(pat, clean_text, re.IGNORECASE):
            return None, f"Question targets a meaningless stopword ('{clean_text[:40]}...')."

    # 2. Validate Options Count & Content
    raw_options = q_data.get("options", [])
    if not isinstance(raw_options, list):
        return None, "Options must be a list."

    cleaned_options = [str(opt).strip() for opt in raw_options if str(opt).strip()]
    if len(cleaned_options) != 4:
        return None, f"Expected exactly 4 options, got {len(cleaned_options)}."

    # Uniqueness check (case-insensitive)
    seen_opts = set()
    for opt in cleaned_options:
        lower_opt = opt.lower()
        if lower_opt in seen_opts:
            return None, f"Duplicate option detected: '{opt}'."
        seen_opts.add(lower_opt)

    # Forbidden meta-phrases check
    for opt in cleaned_options:
        for f_pat in FORBIDDEN_OPTION_PATTERNS:
            if re.search(f_pat, opt, re.IGNORECASE):
                return None, f"Forbidden meta-option phrase ('{opt}') found."

    # 3. Validate Correct Index
    raw_idx = q_data.get("correctIndex") if "correctIndex" in q_data else q_data.get("correct_index", 0)
    try:
        correct_idx = int(raw_idx)
    except (ValueError, TypeError):
        return None, f"Invalid correct index value: {raw_idx}."

    if correct_idx < 0 or correct_idx >= 4:
        return None, f"Correct index {correct_idx} is out of bounds (must be 0-3)."

    correct_option_text = cleaned_options[correct_idx]

    # 4. Balanced Option Length Validation (Dead giveaway prevention)
    correct_len = len(correct_option_text)
    distractor_lens = [len(cleaned_options[i]) for i in range(4) if i != correct_idx]
    avg_distractor_len = sum(distractor_lens) / 3.0

    # If correct option is more than 1.8x the average distractor length (with a small 20-char buffer for short items)
    if avg_distractor_len > 0 and correct_len > (1.8 * avg_distractor_len + 20):
        return None, (
            f"Correct option is disproportionately long ({correct_len} chars vs avg {avg_distractor_len:.1f} chars). "
            "Rejecting question to prevent dead giveaway."
        )

    # 5. Shuffle options so correctIndex is evenly distributed across A, B, C, D
    shuffled_options = list(cleaned_options)
    random.shuffle(shuffled_options)
    new_correct_idx = shuffled_options.index(correct_option_text)

    # 6. Explanation
    explanation = str(q_data.get("explanation", "")).strip()
    if not explanation or len(explanation) < 10:
        explanation = f"'{correct_option_text}' is the correct answer based on concepts covered in {default_topic}."

    # 7. Topic
    topic = str(q_data.get("topic") or q_data.get("topic_tag") or default_topic).strip() or default_topic

    return GeneratedQuestion(
        question_text=clean_text,
        options=shuffled_options,
        correct_index=new_correct_idx,
        explanation=explanation,
        topic_tag=topic,
        difficulty=difficulty,
        order_num=order_num
    ), None


# ==============================================================================
# GEMINI AI EXAM-QUALITY GENERATOR
# ==============================================================================

SYSTEM_PROMPT_TEMPLATE = """Tum ek experienced college professor ho jo MCQ exam-quality questions banata hai, sirf diye gaye study material ke basis par.
- Sawal kisi important concept, definition, difference, working, formula ya application par ho. Kisi aam word ('following', 'given', 'above') ya adhoore vaakya par sawal mat banao.
- Sawal poora, clear aur apne aap mein samajh aane wala ho. 'According to the material' jaisi line ki zaroorat nahi.
- Mix rakho: kuch seedhe concept ke, kuch 'kyun/kaise' wale, kuch chhote numerical ya scenario wale (jahan relevant ho).
- Exactly 4 options. Sirf EK sahi.
- Galat options (distractors) isi topic ke hone chahiye: wo aam galatfehmiyan, milte-julte concepts ya sahi answer ke kareeb galat cheezein jo ek confused student chun sakta hai. Dusre subject ya bilkul unrelated cheezein (jaise COA ke sawal mein Quick Sort) bilkul nahi.
- Saare 4 options ki lambai, bhasha aur style lagbhag ek jaisi ho. Sahi option sabse lamba ya sabse detailed na ho. Material ka text copy-paste mat karo, option apne shabdon mein chhota aur saaf likho (1 line, max ~15 words).
- 'All of the above', 'None of the above', 'Both A and B' jaise options mat banao.
- Sahi option ki position random rakho (A, B, C, D mein barabar). Har sawal ke sath 1-2 line ki explanation do ki sahi kyun sahi hai aur baaki kyun galat.
- Koi sawal repeat ya dohraya hua na ho. Jo cheez material mein nahi hai us par sawal mat banao.

Output MUST be strictly valid JSON conforming exactly to this structure:
{{
  "questions": [
    {{
      "question": "string",
      "options": ["string", "string", "string", "string"],
      "correctIndex": 0,
      "explanation": "string",
      "topic": "string",
      "difficulty": "easy|medium|hard"
    }}
  ]
}}"""


def get_gemini_api_key() -> str:
    """Dynamically retrieves API key from settings or .env file."""
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.lower() in ("your_key_here", "your_api_key_here", "none", ""):
        return settings.GEMINI_API_KEY.strip()
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        load_dotenv(dotenv_path=env_file, override=True)
    return (os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY or "").strip()


def call_gemini_for_questions(
    material_text: str,
    subject_code: str,
    topic: str,
    num_questions: int,
    difficulty: str,
    existing_questions: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Calls Google Gemini using the official Google Gen AI SDK with structured JSON output.
    Attempts model fallbacks if primary model is unavailable.
    """
    api_key = get_gemini_api_key()
    if not api_key or api_key.lower() in ("your_key_here", "your_gemini_api_key_here", "none", ""):
        raise QuizGenerationError(
            "AI abhi setup nahi hai. backend/.env mein valid GEMINI_API_KEY daalein.",
            status_code=400
        )

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        logger.error("google-genai SDK not installed.")
        raise QuizGenerationError("AI library setup adhura hai (google-genai required).", status_code=500)

    client = genai.Client(api_key=api_key)

    primary_model = (os.getenv("GEMINI_MODEL") or settings.GEMINI_MODEL or "gemini-3.5-flash-lite").strip()
    candidate_models = [primary_model]
    for fb in ["gemini-3.5-flash-lite", "gemini-3-flash-preview", "gemini-3.8-flash"]:
        if fb not in candidate_models:
            candidate_models.append(fb)

    # Prompt specification
    avoid_block = ""
    if existing_questions and len(existing_questions) > 0:
        avoid_list = "\n".join([f"- {q}" for q in existing_questions[:10]])
        avoid_block = f"\nDo NOT repeat or duplicate the following existing questions:\n{avoid_list}\n"

    user_prompt = (
        f"Generate exactly {num_questions} high-quality, exam-grade multiple-choice questions (MCQs) grounded exclusively on the study material below.\n"
        f"Subject Code: {subject_code}\n"
        f"Topic Focus: {topic}\n"
        f"Target Difficulty: {difficulty}\n"
        f"{avoid_block}\n"
        f"Study Material Excerpt:\n"
        f"\"\"\"\n{material_text[:12000]}\n\"\"\"\n"
    )

    last_error: Optional[Exception] = None

    for model_name in candidate_models:
        try:
            print(f"[QUIZ AI] Requesting {num_questions} questions from model: '{model_name}' (Subject: {subject_code}, Topic: {topic})...", flush=True)
            response = client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT_TEMPLATE,
                    response_mime_type="application/json",
                    temperature=0.3
                )
            )

            if not response or not response.text:
                continue

            raw_json = json.loads(response.text.strip())
            questions_list = []
            if isinstance(raw_json, dict) and "questions" in raw_json:
                questions_list = raw_json["questions"]
            elif isinstance(raw_json, list):
                questions_list = raw_json

            if questions_list and len(questions_list) > 0:
                print(f"[QUIZ AI] Received {len(questions_list)} raw questions from '{model_name}'.", flush=True)
                return questions_list

        except Exception as exc:
            last_error = exc
            print(f"[QUIZ AI WARNING] Model '{model_name}' failed: {type(exc).__name__}: {exc}", flush=True)
            logger.warning(f"Model '{model_name}' failed: {exc}", exc_info=True)
            continue

    # All models failed
    err_str = str(last_error) if last_error else "No output from AI models"
    print(f"[QUIZ AI ERROR] All model attempts failed. Last error: {err_str}", flush=True)

    if "API_KEY_INVALID" in err_str or "invalid api key" in err_str.lower():
        raise QuizGenerationError("Aapki GEMINI_API_KEY galat ya expired hai. Kripya .env mein sahi key daalein.", status_code=400)
    elif "429" in err_str or "quota" in err_str.lower():
        raise QuizGenerationError("Gemini API rate limit reach ho gayi hai. Kripya kuch second intezar karein.", status_code=429)
    elif "503" in err_str or "high demand" in err_str.lower():
        raise QuizGenerationError("AI servers par temporary traffic hai. Kripya Retry button par click karein.", status_code=503)
    else:
        raise QuizGenerationError(f"Quiz generate karne mein samasya aayi ({type(last_error).__name__}). Kripya Retry karein.", status_code=500)


# ==============================================================================
# MAIN QUIZ GENERATION PIPELINE
# ==============================================================================

async def generate_quiz_pipeline(
    extracted_text: str,
    subject_code: str,
    topic: Optional[str],
    num_questions: int,
    difficulty: str
) -> Tuple[List[GeneratedQuestion], str]:
    """
    Orchestrates quiz generation exclusively via Google Gemini AI:
    1. Validates text adequacy (minimum 100 chars).
    2. Calls Gemini with custom college professor exam-grade instructions.
    3. Validates each generated question against strict academic criteria.
    4. Automatically retries missing/rejected questions (up to 2 retries).
    5. Shuffles option positions on backend.
    Returns (validated_questions, 'ai').
    """
    clean_text = extracted_text.strip() if extracted_text else ""
    if len(clean_text) < MIN_TEXT_LENGTH_FOR_QUIZ:
        raise QuizGenerationError(
            f"Selected document contains insufficient text ({len(clean_text)} characters, minimum {MIN_TEXT_LENGTH_FOR_QUIZ} required). "
            "Kripya thoda bada aur syllabus text wala material upload karein.",
            status_code=400
        )

    topic_label = topic.strip() if topic and topic.strip() else f"Subject {subject_code}"
    validated_questions: List[GeneratedQuestion] = []
    used_question_texts: set[str] = set()

    # Pass 1: Initial generation
    raw_questions = call_gemini_for_questions(
        material_text=clean_text,
        subject_code=subject_code,
        topic=topic_label,
        num_questions=num_questions,
        difficulty=difficulty
    )

    for q_data in raw_questions:
        q_obj, reject_reason = validate_and_sanitize_question(
            q_data=q_data,
            default_topic=topic_label,
            difficulty=difficulty,
            order_num=len(validated_questions) + 1
        )
        if q_obj and q_obj.question_text.lower() not in used_question_texts:
            used_question_texts.add(q_obj.question_text.lower())
            validated_questions.append(q_obj)
        elif reject_reason:
            print(f"[QUIZ VALIDATION REJECT] {reject_reason}", flush=True)

    # Retry loop: if some questions failed validation, request just the delta (max 2 retries)
    retries = 0
    while len(validated_questions) < num_questions and retries < 2:
        needed = num_questions - len(validated_questions)
        retries += 1
        print(f"[QUIZ AI RETRY {retries}] Requesting {needed} replacement questions...", flush=True)
        try:
            retry_raw = call_gemini_for_questions(
                material_text=clean_text,
                subject_code=subject_code,
                topic=topic_label,
                num_questions=needed,
                difficulty=difficulty,
                existing_questions=list(used_question_texts)
            )
            for q_data in retry_raw:
                if len(validated_questions) >= num_questions:
                    break
                q_obj, reject_reason = validate_and_sanitize_question(
                    q_data=q_data,
                    default_topic=topic_label,
                    difficulty=difficulty,
                    order_num=len(validated_questions) + 1
                )
                if q_obj and q_obj.question_text.lower() not in used_question_texts:
                    used_question_texts.add(q_obj.question_text.lower())
                    validated_questions.append(q_obj)
                elif reject_reason:
                    print(f"[QUIZ VALIDATION RETRY REJECT] {reject_reason}", flush=True)
        except Exception as retry_err:
            print(f"[QUIZ AI RETRY ERROR] {retry_err}", flush=True)
            break

    if len(validated_questions) == 0:
        raise QuizGenerationError(
            "Quiz questions validation mein fail ho gaye. Kripya thoda aur text wala material use karein aur dobara try karein.",
            status_code=500
        )

    # Re-assign sequential order numbers
    for idx, q in enumerate(validated_questions, 1):
        q.order_num = idx

    print(f"[QUIZ GENERATION SUCCESS] {len(validated_questions)} exam-quality questions generated and verified.", flush=True)
    return validated_questions[:num_questions], "ai"
