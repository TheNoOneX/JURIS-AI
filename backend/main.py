"""
NyayaConnect Backend (v4.0 – Classified + Verbosity Routed)
----------------------------------------------------------

KEY FEATURES:
- Document classification (agreement, govt notice, court notice, university circular, insurance)
- Verbosity control: basic / medium / advanced
- Section enforcement (laws, references ALWAYS populated)
- OCR → Vision fallback
- Strict JSON output
- Backward compatible with old frontend
"""

# ======================================================
# 0. IMPORTS
# ======================================================

import os
import io
import re
import json
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

import pytesseract
import pdfplumber
from docx import Document

from google import genai


# ======================================================
# 1. STARTUP & ENV
# ======================================================

print("🔧 Loading environment variables...")
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise RuntimeError("❌ GOOGLE_API_KEY missing")

print("✅ Environment variables injected")

print("🔌 Connecting to Gemini...")
client = genai.Client(api_key=API_KEY)
MODEL_NAME = "gemini-2.5-flash"
print(f"✅ Gemini connected | Model = {MODEL_NAME}")

app = FastAPI(title="NyayaConnect Backend", version="4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

print("🚀 FastAPI initialized")


# ======================================================
# 2. SYSTEM PROMPT (BASE – UNCHANGED PHILOSOPHY)
# ======================================================

SYSTEM_PROMPT = """
You are NyayaConnect, an AI legal assistant for India.

CORE RULES:
- Always return VALID JSON only
- Never hallucinate laws or cases
- Risk scoring must be strict
- Explain clearly, not legally advise
- Prefer Bharatiya Nyaya Sanhita (BNS) where applicable
"""


# ======================================================
# 3. VERBOSITY STYLES (NEW – ADDITIVE)
# ======================================================

PROMPT_STYLE = {
    "basic": """
STYLE:
- Extremely simple language
- 1–2 sentence summary
- Minimal explanation
""",
    "medium": """
STYLE:
- Explain WHY clauses or notices are risky
- Simple language but informative
- Each red flag must have reasoning
""",
    "advanced": """
STYLE:
- Judicial and statutory focus
- Mention Acts + Section numbers
- Explain enforceability and unfairness
- Still simple, not academic
"""
}

def get_style(verbosity: str) -> str:
    return PROMPT_STYLE.get(verbosity, PROMPT_STYLE["basic"])


# ======================================================
# 4. DOCUMENT CLASSIFICATION (RESTORED & IMPROVED)
# ======================================================

def classify_document(text: str) -> str:
    """
    Lightweight hybrid classifier.
    Safe defaults, no breaking behavior.
    """
    t = text.lower()

    if any(k in t for k in ["university", "exam", "semester", "admission", "circular"]):
        return "university_circular"

    if any(k in t for k in ["court", "summon", "legal notice", "section", "hereby"]):
        return "court_notice"

    if any(k in t for k in ["gazette", "ministry", "government", "department"]):
        return "government_notice"

    if any(k in t for k in ["policy", "insurance", "premium", "claim"]):
        return "insurance_policy"

    return "agreement"


# ======================================================
# 5. REFERENCE REGISTRY (CURATED & STABLE)
# ======================================================

REFERENCE_MAP = {
    "contract": {
        "title": "Indian Contract Act, 1872",
        "url": "https://www.indiacode.nic.in/handle/123456789/1566"
    },
    "consumer": {
        "title": "Consumer Protection Act, 2019",
        "url": "https://www.indiacode.nic.in/handle/123456789/1520"
    },
    "bns": {
        "title": "Bharatiya Nyaya Sanhita, 2023",
        "url": "https://www.indiacode.nic.in"
    },
    "supreme_court": {
        "title": "Supreme Court of India",
        "url": "https://main.sci.gov.in"
    }
}


# ======================================================
# 6. PROMPT BUILDER (MERGED LOGIC)
# ======================================================

def build_prompt(text: str, doc_type: str, language: str, verbosity: str) -> str:
    style = get_style(verbosity)

    return f"""
{SYSTEM_PROMPT}

{style}

DOCUMENT TYPE: {doc_type}

TASK:
Analyze the document below and populate ALL JSON fields.
- laws: MUST contain relevant Acts or sections
- references: MUST contain valid links
- actions: practical next steps
- risk_score: 0–100
- risk_level: LOW / MEDIUM / HIGH

TEXT:
\"\"\"{text[:10000]}\"\"\"

Language: {language}

RETURN JSON:
{{
  "summary": "",
  "final_summary": [],
  "risk_score": 0,
  "risk_level": "",
  "red_flags": [],
  "laws": [],
  "actions": [],
  "references": [],
  "disclaimer": "Educational purpose only. Consult a lawyer."
}}
"""


# ======================================================
# 7. JSON PARSER (SAFE)
# ======================================================

def extract_json(text: str) -> dict:
    try:
        match = re.search(r"\{[\s\S]*\}", text)
        return json.loads(match.group())
    except Exception:
        return {
            "summary": "Could not analyze clearly.",
            "final_summary": [],
            "risk_score": 50,
            "risk_level": "MEDIUM",
            "red_flags": ["Parsing error"],
            "laws": ["Indian law applicable"],
            "actions": ["Consult a lawyer"],
            "references": [REFERENCE_MAP["contract"]],
            "disclaimer": "Educational purpose only. Consult a lawyer."
        }


# ======================================================
# 8. TEXT EXTRACTION
# ======================================================

def extract_text_from_image(image: Image.Image) -> str:
    try:
        return pytesseract.image_to_string(image)
    except:
        return ""

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for p in pdf.pages:
            text += p.extract_text() or ""
    return text

def extract_text_from_doc(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


# ======================================================
# 9. ROUTES
# ======================================================

@app.get("/")
def root():
    return {"status": "online", "message": "NyayaConnect Backend v4.0 running"}


@app.post("/api/analyze-text")
async def analyze_text(
    problem: str = Form(...),
    language: str = Form("English"),
    verbosity: str = Form("basic")
):
    print(f"📨 Text request | verbosity={verbosity}")

    prompt = build_prompt(problem, "agreement", language, verbosity)
    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    return extract_json(response.text)


@app.post("/api/analyze-image")
async def analyze_image(
    file: UploadFile = File(...),
    language: str = Form("English"),
    verbosity: str = Form("basic")
):
    print(f"📨 Document received | {file.content_type}")

    file_bytes = await file.read()
    text = ""

    if file.content_type.startswith("image/"):
        image = Image.open(io.BytesIO(file_bytes))
        text = extract_text_from_image(image)

        if not text.strip():
            print("📸 OCR failed → Vision fallback")
            prompt = build_prompt("Analyze this image.", "agreement", language, verbosity)
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[prompt, image]
            )
            return extract_json(response.text)

    elif file.content_type == "application/pdf":
        text = extract_text_from_pdf(file_bytes)

    elif file.content_type in [
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]:
        text = extract_text_from_doc(file_bytes)

    else:
        raise HTTPException(400, "Unsupported file type")

    if not text.strip():
        raise HTTPException(400, "No readable text found")

    doc_type = classify_document(text)
    print(f"📄 Classified as: {doc_type}")

    prompt = build_prompt(text, doc_type, language, verbosity)
    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    return extract_json(response.text)
