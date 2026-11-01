import os
import json
import re
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from backend.app.config import BASE_DIR, settings
from backend.app.models.material import LearningMaterial
from backend.app.models.material_topic import MaterialTopic

logger = logging.getLogger("edumind.curriculum")


def get_gemini_api_key() -> str:
    """Dynamically retrieves API key from settings or .env file."""
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.lower() not in ("your_key_here", "your_api_key_here", "none", ""):
        return settings.GEMINI_API_KEY.strip()
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        load_dotenv(dotenv_path=env_file, override=True)
    return (os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY or "").strip()


def heuristic_fallback_topics(material_text: str, material_title: str) -> Dict[str, Any]:
    """
    Resilient offline/fallback heading extractor that divides document into logical
    chapters and subtopics if AI API is unreachable. Guarantees at least 3 topics.
    """
    clean_lines = [line.strip() for line in material_text.splitlines() if line.strip()]
    potential_headings = []

    for line in clean_lines[:150]:
        # Filter common non-heading text
        if len(line) < 4 or len(line) > 85:
            continue
        if line.lower().startswith(("page ", "http", "copyright", "all rights")):
            continue
        # Check if line looks like heading: Title case, all caps, or starts with unit/chapter/section
        is_heading_pattern = bool(
            re.match(r'^(unit\s*\d+|chapter\s*\d+|\d+\.\d+|\b[A-Z0-9\s\-\:\&\,]{4,}\b)', line, re.IGNORECASE)
            or (line.istitle() and len(line.split()) <= 8)
        )
        if is_heading_pattern and line not in potential_headings:
            potential_headings.append(line)

    # If few headings found, split by paragraphs
    if len(potential_headings) < 3:
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', material_text) if len(p.strip()) > 80]
        for idx, p in enumerate(paragraphs[:6], 1):
            first_sentence = p.split('.')[0].strip()
            topic_title = first_sentence[:60] if len(first_sentence) > 5 else f"Core Concept {idx}"
            if topic_title not in potential_headings:
                potential_headings.append(topic_title)

    # Ensure at least 3 topics
    if len(potential_headings) < 3:
        base = material_title or "Subject Overview"
        potential_headings = [
            f"{base}: Fundamentals & Definitions",
            f"{base}: Architecture & Working Mechanism",
            f"{base}: Advanced Applications & Operations"
        ]

    # Group into 1-3 chapters
    chapters = []
    chunk_size = max(3, len(potential_headings) // 2) if len(potential_headings) >= 6 else len(potential_headings)
    
    chap1_topics = potential_headings[:chunk_size]
    chapters.append({
        "title": f"{material_title} - Core Principles",
        "topics": [
            {
                "title": title,
                "summary": f"Key concepts, definitions, and operational mechanisms of {title}.",
                "estimatedMinutes": 15
            }
            for title in chap1_topics
        ]
    })

    if len(potential_headings) > chunk_size:
        chap2_topics = potential_headings[chunk_size:]
        chapters.append({
            "title": f"{material_title} - Applied Concepts & Design",
            "topics": [
                {
                    "title": title,
                    "summary": f"In-depth analysis, structural organization, and practical examples for {title}.",
                    "estimatedMinutes": 20
                }
                for title in chap2_topics
            ]
        })

    return {"chapters": chapters}


def extract_curriculum_topics(
    db: Session,
    material_id: int,
    user_id: str,
    subject_code: str,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Extracts structured chapters and subtopics for a learning material:
    1. Checks cached syllabus in DB.
    2. Calls Gemini API with structured JSON output if not cached or forced.
    3. Falls back gracefully to heuristic extractor if AI call fails.
    4. Persists the result into `learning_materials.syllabus_json` and `material_topics` table.
    """
    material = db.query(LearningMaterial).filter(LearningMaterial.id == material_id).first()
    if not material:
        return {"chapters": []}

    # 1. Check existing cached syllabus
    if not force_refresh and material.syllabus_json:
        try:
            cached_data = json.loads(material.syllabus_json)
            if cached_data.get("chapters") and len(cached_data["chapters"]) > 0:
                return cached_data
        except Exception:
            pass

    extracted_text = material.extracted_text or ""
    material_title = material.title or material.file_name or "Study Material"

    data: Optional[Dict[str, Any]] = None

    # 2. Attempt AI Generation with Gemini
    api_key = get_gemini_api_key()
    if api_key and len(extracted_text.strip()) >= 100:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            model_name = (os.getenv("GEMINI_MODEL") or settings.GEMINI_MODEL or "gemini-3.5-flash-lite").strip()

            prompt = f"""Tum ek expert college syllabus designer ho.
Diye gaye engineering study material ko analyze karo aur use logical chapters aur har chapter ke andar 3-8 chhote topics mein divide karo.
- Chapter aur topic ke naam material ke asli concepts aur headings se hone chahiye (jaise 'Memory Hierarchy', 'Main Memory & Bootstrap Loader', 'Associative Memory', 'Cache Mapping Techniques', 'Virtual Memory & Page Table').
- File ka naam ya 'Chapter 1' jaisa generic naam bilkul mat use karo.
- Agar material chhota bhi ho to bhi kam se kam 3 distinct topics hone chahiye.
- Har topic ka ek concise 1-2 line ka summary aur realistic estimated study minutes do (10-30 mins).

Return ONLY valid JSON matching this schema:
{{
  "chapters": [
    {{
      "title": "string",
      "topics": [
        {{
          "title": "string",
          "summary": "string",
          "estimatedMinutes": 15
        }}
      ]
    }}
  ]
}}

STUDY MATERIAL TEXT:
{extracted_text[:14000]}
"""

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )

            if response and response.text:
                parsed = json.loads(response.text.strip())
                if parsed.get("chapters") and len(parsed["chapters"]) > 0:
                    data = parsed
                    logger.info(f"[CURRICULUM AI SUCCESS] Extracted {len(data['chapters'])} chapters for material {material_id}")
        except Exception as exc:
            logger.warning(f"[CURRICULUM AI FALLBACK] AI extraction failed: {exc}. Falling back to heuristic extractor.")

    # 3. Fallback to heuristic parser if AI failed or no text
    if not data or not data.get("chapters"):
        data = heuristic_fallback_topics(extracted_text, material_title)

    # 4. Save and persist in DB
    try:
        material.syllabus_json = json.dumps(data)
        
        # Clear existing topics for this material
        db.query(MaterialTopic).filter(MaterialTopic.material_id == material_id).delete()

        # Insert fresh records into material_topics table
        global_order = 1
        for chap_idx, ch in enumerate(data.get("chapters", []), 1):
            chap_title = ch.get("title", f"Chapter {chap_idx}").strip()
            for tp in ch.get("topics", []):
                tp_title = tp.get("title", f"Topic {global_order}").strip()
                tp_summary = tp.get("summary", "").strip()
                est_mins = int(tp.get("estimatedMinutes", 15))

                topic_rec = MaterialTopic(
                    material_id=material.id,
                    user_id=str(user_id),
                    subject_code=subject_code,
                    chapter_title=chap_title,
                    chapter_order=chap_idx,
                    topic_title=tp_title,
                    topic_summary=tp_summary,
                    estimated_minutes=est_mins,
                    order_num=global_order
                )
                db.add(topic_rec)
                global_order += 1

        db.commit()
        db.refresh(material)
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to persist material topics: {exc}")

    return data

