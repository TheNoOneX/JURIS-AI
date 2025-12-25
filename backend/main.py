"""
Juris-AI Backend – main.py (Merged & Stabilized)

Upgrades:
- Invariant response schema
- Verbosity depth enforcement
- Frontend-safe outputs
- No regression of existing logic
"""

# ======================================================
# IMPORTS (UNCHANGED + REQUIRED)
# ======================================================

import os
import io
import re
import json
import base64
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

import pytesseract
import pdfplumber
from docx import Document
from google import genai


# ======================================================
# ENV & APP INIT (PRESERVED)
# ======================================================

print("🔧 Loading environment variables...")
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ GOOGLE_API_KEY missing")

print("🔌 Connecting to Gemini...")
client = genai.Client(api_key=API_KEY)
MODEL_NAME = "gemini-2.5-flash"
print("✅ Gemini connected")

app = FastAPI(title="NyayaConnect Backend", version="5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

print("🚀 FastAPI initialized")


# ======================================================
# SYSTEM PROMPT (ENHANCED, NOT REPLACED)
# ======================================================

SYSTEM_PROMPT = """
You are JURIS AI, an Indian legal risk analysis assistant.

CRITICAL OUTPUT RULES (NON-NEGOTIABLE):
1. Output ONLY valid JSON.
2. ALL fields MUST exist.
3. ALL list fields MUST be FLAT ARRAYS OF STRINGS.
4. DO NOT return objects, dictionaries, or nested structures.
5. DO NOT group items or use categories.
6. Verbosity affects DEPTH ONLY, never structure.
7. Never hallucinate laws or cases.

Risk Rules:
- HIGH: score > 70
- MEDIUM: score 40–70
- LOW: score < 40
"""


# ======================================================
# VERBOSITY CONTEXT (IMPROVED)
# ======================================================

PROMPT_STYLE = {
    "basic": """
VERBOSITY MODE: BASIC
- Very simple language
- Assume no legal knowledge
- 1–2 short sentences per point
- No section numbers
- Focus only on user impact
""",
    "medium": """
VERBOSITY MODE: MEDIUM
- Explain WHY something is risky
- Mention law names (no sections)
- Explain consequences clearly
- Simple but informative
""",
    "advanced": """
VERBOSITY MODE: ADVANCED
- Detailed legal reasoning
- Mention Acts AND Section numbers
- Explain enforceability and principles
- No case law dumping
"""
}

def get_style(verbosity: str) -> str:
    return PROMPT_STYLE.get(verbosity, PROMPT_STYLE["basic"])


# ======================================================
# LANGUAGE RULE (PRESERVED + STRENGTHENED)
# ======================================================

def language_rule(language: str) -> str:
    return f"""
LANGUAGE RULE:
- Respond ONLY in {language}
- Explain legal terms in {language}
"""


# ======================================================
# DOCUMENT CLASSIFICATION (PRESERVED)
# ======================================================

def classify_document(text: str) -> str:
    t = text.lower()

    if any(k in t for k in ["exam", "university", "semester", "controller of examinations"]):
        return "university_circular"
    if any(k in t for k in ["legal notice", "summons", "advocate", "high court"]):
        return "court_notice"
    if any(k in t for k in ["gazette", "ministry", "government of india"]):
        return "government_notice"
    if any(k in t for k in ["insurance", "policy number", "sum insured"]):
        return "insurance_policy"

    return "agreement"


# ======================================================
# PROMPT BUILDER (MERGED)
# ======================================================

def build_prompt(text: str, doc_type: str, language: str, verbosity: str) -> str:
    return f"""
{SYSTEM_PROMPT}

{language_rule(language)}

{get_style(verbosity)}

DOCUMENT TYPE: {doc_type}

TASK:
Analyze the document below and populate ALL fields.
Follow output rules strictly.

TEXT:
\"\"\"{text[:10000]}\"\"\"

RETURN JSON:
{{
  "summary": "",
  "red_flags": [],
  "laws": [],
  "actions": [],
  "final_summary": [],
  "references": [],
  "risk_score": 0,
  "risk_level": ""
}}
"""


# ======================================================
# GEMINI CALL (COMPATIBLE & SAFE)
# ======================================================

def call_gemini(prompt: str, file_part=None):
    """
    Unified Gemini caller.
    Supports text-only OR text + raw file (image/pdf/doc).
    """
    parts = [{"text": prompt}]

    if file_part:
        parts.append(file_part)

    return client.models.generate_content(
        model=MODEL_NAME,
        contents=[{"role": "user", "parts": parts}]
    )


# ======================================================
# JSON EXTRACTION (PRESERVED + SAFER)
# ======================================================

def extract_json(text: str) -> dict:
    try:
        match = re.search(r"\{[\s\S]*\}", text)
        return json.loads(match.group())
    except Exception as e:
        print("❌ JSON parse error:", e)
        return {}


# ======================================================
# SCHEMA ENFORCEMENT (NEW – CORE FIX)
# ======================================================

def enforce_schema(data: dict) -> dict:
    def flat(value):
        if isinstance(value, list):
            return [str(v) for v in value]
        if isinstance(value, dict):
            return [str(v) for v in value.values()]
        if isinstance(value, str):
            return [value]
        return []

    score = int(data.get("risk_score", 50))
    if score > 70:
        level = "HIGH"
    elif score >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"

    refs = flat(data.get("references"))
    if len(refs) < 2:
        refs += [
            "https://www.indiacode.nic.in",
            "https://main.sci.gov.in"
        ]

    return {
        "summary": str(data.get("summary", "")),
        "red_flags": flat(data.get("red_flags")),
        "laws": flat(data.get("laws")),
        "actions": flat(data.get("actions")),
        "final_summary": flat(data.get("final_summary")),
        "references": refs[:5],
        "risk_score": score,
        "risk_level": level
    }


# ======================================================
# TEXT EXTRACTION (PRESERVED)
# ======================================================

def extract_text_from_image(image):
    try:
        return pytesseract.image_to_string(image)
    except Exception as e:
        print("❌ OCR error:", e)
        return ""
    


def make_file_part(file_bytes: bytes, mime_type: str):
    """
    Converts raw file bytes into a Gemini-compatible inline_data part.
    Used for scanned PDFs, images, or any unreadable document.
    """
    return {
        "inline_data": {
            "mime_type": mime_type,
            "data": base64.b64encode(file_bytes).decode("utf-8")
        }
    }


def extract_text_from_pdf(b):
    try:
        text = ""
        with pdfplumber.open(io.BytesIO(b)) as pdf:
            for p in pdf.pages:
                text += p.extract_text() or ""
        return text
    except Exception as e:
        print("❌ PDF parse error:", e)
        return ""

def extract_text_from_doc(b):
    try:
        doc = Document(io.BytesIO(b))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        print("❌ DOC parse error:", e)
        return ""


# ======================================================
# ROUTES (UNCHANGED SIGNATURES)
# ======================================================

@app.get("/")
def root():
    return {"status": "online"}

@app.post("/api/analyze-text")
async def analyze_text(
    problem: str = Form(...),
    language: str = Form("English"),
    verbosity: str = Form("basic")
):
    print(f"📨 Text analysis | lang={language} | verbosity={verbosity}")
    prompt = build_prompt(problem, "agreement", language, verbosity)
    response = call_gemini(prompt)
    return enforce_schema(extract_json(response.text))


@app.post("/api/analyze-image")
async def analyze_image(
    file: UploadFile = File(...),
    language: str = Form("English"),
    verbosity: str = Form("basic")
):
    print(f"📨 Document received: {file.filename}")
    data = await file.read()
    text = ""

    if file.content_type.startswith("image/"):
        image = Image.open(io.BytesIO(data))
        text = extract_text_from_image(image)

        if not text.strip():
            print("📸 OCR empty → Vision fallback")
            prompt = build_prompt("Analyze image content.", "agreement", language, verbosity)
            response = call_gemini(prompt, image=image)
            return enforce_schema(extract_json(response.text))

    elif file.content_type == "application/pdf":
        text = extract_text_from_pdf(data)

    elif file.content_type in [
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]:
        text = extract_text_from_doc(data)

    if not text.strip():
        print("📄 Text extraction failed → using raw document Gemini fallback")

        file_part = make_file_part(data, file.content_type)

        prompt = build_prompt(
            "Analyze the uploaded document directly.",
            "unknown",
            language,
            verbosity
        )

        response = call_gemini(prompt, file_part=file_part)
        return enforce_schema(extract_json(response.text))

    
    doc_type = classify_document(text)
    print(f"📄 Classified as: {doc_type}")

    prompt = build_prompt(text, doc_type, language, verbosity)
    response = call_gemini(prompt)
    return enforce_schema(extract_json(response.text))
