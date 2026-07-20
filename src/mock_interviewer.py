"""Offline AI Recruiter Simulation & Mock Interviewer Copilot.

Generates tailored technical interview questions and simulates an HR / hiring manager
call by comparing candidate profile skills against target job description requirements.
Supports local GGUF models via Ollama (zero-cost, zero-key, private).
"""
from __future__ import annotations

import json
import os
import uuid
from typing import Any

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

from . import config, llm
from .profile_parser import profile_context


def generate_tts_audio(text: str) -> str | None:
    """Generates offline TTS audio for a given text and returns the file path."""
    if not pyttsx3:
        return None
    
    # Ensure audio directory exists
    output_dir = os.path.join(os.getcwd(), "data", "audio")
    os.makedirs(output_dir, exist_ok=True)
    
    file_name = f"{uuid.uuid4().hex}.wav"
    output_path = os.path.join(output_dir, file_name)
    
    try:
        engine = pyttsx3.init()
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        # Reset the engine so it doesn't get stuck on subsequent calls
        engine.stop()
        return output_path
    except Exception as e:
        print(f"TTS Generation failed: {e}")
        return None


def generate_interview_questions(job: dict[str, Any], profile: dict[str, Any], num_questions: int = 4) -> list[dict[str, str]]:
    """Generate targeted technical and behavioural interview questions."""
    prefs = config.load_prefs()
    jd = (job.get("description") or "")[:2000]
    role = job.get("title") or "Software Engineer"
    company = job.get("company") or "the company"
    
    prompt = (
        f"You are a principal engineering hiring manager at {company} interviewing a candidate for {role}.\n"
        f"Job Description excerpt:\n{jd}\n\n"
        "Based on the candidate's profile context and the job description above, "
        f"generate {num_questions} challenging, highly specific interview questions.\n"
        "Focus on:\n"
        "1. Technical deep-dives into skills required by the JD where the candidate has relevant projects.\n"
        "2. Bridging gaps where the JD asks for a tool/scale the candidate hasn't explicitly listed.\n"
        "3. A system design or architecture tradeoff question relevant to the company's domain.\n\n"
        "Return a JSON array of objects: [{\"category\": \"Technical|System Design|Gap Bridge\", \"question\": \"...\", \"rationale\": \"Why you are asking this based on their resume/JD\"}]."
    )
    
    data = llm.generate_json(
        prompt,
        system="You are an insightful, rigorous technical interviewer. Return ONLY valid JSON array.",
        cached_context=profile_context(profile),
        model=prefs.get("writing_model"),
        max_tokens=1000,
    )
    questions = []
    if isinstance(data, list):
        questions = [dict(q) if isinstance(q, dict) else {"question": str(q)} for q in data]
    elif isinstance(data, dict) and "questions" in data and isinstance(data["questions"], list):
        questions = [dict(q) if isinstance(q, dict) else {"question": str(q)} for q in data["questions"]]
    else:
        questions = [{
            "category": "General",
            "question": f"Tell me about your experience relevant to {role} at {company}.",
            "rationale": "Standard introductory question."
        }]

    # Generate TTS audio for each question
    for q in questions:
        if "question" in q:
            audio_path = generate_tts_audio(q["question"])
            if audio_path:
                q["audio_path"] = audio_path

    return questions
