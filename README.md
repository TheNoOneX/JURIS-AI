# ⚖️ JURIS
Judicial Understanding & Risk Intelligence System

Democratizing Justice for the New India 🇮🇳
Making legal understanding simple, accessible, and AI-powered.

# 📌 Problem Statement

In India, legal language is often:

Too complex for common citizens

Difficult to understand without a lawyer

Scattered across multiple laws and sources

This results in:

People not knowing their rights

Poor legal decision-making

Fear and confusion around judicial processes

# 💡 Solution – What is JURIS?

JURIS is an AI-powered judicial intelligence platform that helps users:

Understand legal problems in simple language

Analyze legal risk levels

Get actionable next steps

Interact via text, voice, or documents

Access the system in multiple Indian languages

All this is done without replacing lawyers, but by empowering citizens with clarity and awareness.

# 🧠 Key Features

🌐 Multilingual Support (English, Hindi, Marathi, Telugu, Tamil)

✍️ Text-based Legal Queries

🎙️ Voice-based Legal Queries

📄 Legal Document Upload & Analysis

⚠️ AI-based Risk Scoring & Visualization

🔊 Text-to-Speech for Accessibility

📚 Authoritative Legal References

📱 Mobile-friendly UI

🔐 Secure AI Integration (Server-side)

# SYSTEM ARCHITECTURE

Frontend (HTML / CSS / JS)
        |
        |  HTTPS Requests (POST)
        v
FastAPI Backend (Python)
        |
        |  Prompt Engineering + Context
        v
Google Gemini AI
        |
        v
Structured Legal Intelligence
        |
        v
Frontend Visualization

# 🖥️ Tech Stack
🎨 Frontend

HTML5

CSS3

JavaScript (Vanilla JS)

Web Speech API (Voice Input & Output)

⚙️ Backend

Python

FastAPI

Uvicorn (ASGI Server)

☁️ Hosting

Backend: Render

Frontend: Netlify

# 🤖 Google Technologies Used

This project actively uses Google’s AI ecosystem:

🔹 Google Gemini API

Core AI engine for legal understanding

Used for:

Legal text analysis

Simplification of judicial language

Risk assessment

Actionable suggestions

Integrated securely via FastAPI (server-side only)

🔹 Gemini 3 (Prompt Debugging & Optimization)

Used during development for:

Prompt testing

Response quality evaluation

Debugging hallucinations

Improving legal accuracy

Helped refine:

Risk classification logic

Output structuring

Multi-language consistency

⚠️ Note: Gemini is used as an assistive intelligence, not as a legal authority.
All outputs are informational, not legal advice.

# 🔐 Security & Privacy

❌ No AI API keys exposed on frontend

🔒 Gemini API key stored as environment variable

🔁 Frontend communicates only with backend

🌐 HTTPS enabled (required for voice features)

🔄 Application Flow

User selects language

Chooses input method:

Write

Speak

Upload document

Frontend sends data to FastAPI

Backend:

Builds structured prompt

Calls Gemini API

Parses AI response

Frontend displays:

Summary

Risk level

Laws applied

Next steps

References

# 📊 Risk Intelligence System

JURIS provides:

Risk Score (0–100%)

Risk Level:

LOW → Safe

MEDIUM → Moderate Risk

HIGH → High Risk (Warning)

Risk is visualized using:

Animated progress

Color-coded badges

Human-readable explanations

# 🌍 Accessibility & Inclusion

Multilingual interface

Voice input for low-literacy users

Text-to-speech output

Mobile-first design

# 🚀 Deployment
Backend

Hosted on Render

FastAPI + Uvicorn

Secure environment variables

Frontend

Hosted on Netlify

Static deployment

HTTPS enabled

# 🧪 How to Run Locally
Backend
pip install -r requirements.txt
uvicorn main:app --reload

Frontend
# Open index.html directly
# or use Live Server

# DISCLAIMER
JURIS is an AI-powered legal awareness tool.
It does not replace lawyers or courts and should not be treated as official legal advice.

# 🏁 Conclusion

JURIS bridges the gap between law and common citizens using responsible AI.
It empowers people with understanding, awareness, and confidence—one legal query at a time.


