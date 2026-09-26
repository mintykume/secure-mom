import os
import shutil
import uuid

from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .asr import transcribe_audio
from .llm_extract import extract_decisions
from .mom_generator import generate_mom_markdown
from .mailer import send_mom_email

app = FastAPI(title="Secure MOM")

os.makedirs(config.UPLOADS_DIR, exist_ok=True)
os.makedirs(config.OUTPUT_DIR, exist_ok=True)


@app.post("/api/process")
async def process_meeting(file: UploadFile, meeting_type: str = Form(...)):
    meeting_id = str(uuid.uuid4())[:8]
    audio_path = os.path.join(config.UPLOADS_DIR, f"{meeting_id}_{file.filename}")

    with open(audio_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # 1. ASR
    transcript = transcribe_audio(audio_path)

    # 2. Local LLM extraction
    extraction = extract_decisions(transcript["text"])

    # 3. MoM document
    mom_markdown = generate_mom_markdown(
        meeting_type=meeting_type,
        meeting_id=meeting_id,
        extraction=extraction,
        detected_language=transcript["detected_language"],
        transcript_excerpt=transcript["text"],
    )
    out_path = os.path.join(config.OUTPUT_DIR, f"{meeting_id}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(mom_markdown)

    # 4. Local email delivery
    send_mom_email(subject=f"MoM — {meeting_type} — {meeting_id}", body_markdown=mom_markdown)

    return JSONResponse(
        {
            "meeting_id": meeting_id,
            "meeting_type": meeting_type,
            "detected_language": transcript["detected_language"],
            "mom_markdown": mom_markdown,
            "action_items": extraction.get("action_items", []),
        }
    )


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Serve the static frontend last, so /api/* routes above take priority.
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
