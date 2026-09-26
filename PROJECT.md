# PROJECT.md — Secure MOM

Context file for every AI coding session on this repo. Paste this whole file
in when you start a new chat with an AI assistant so it doesn't reinvent the
architecture.

## Goal
An on-premise AI pipeline that turns a hospital meeting recording into a
structured Minutes of Meeting (MoM) — decisions, owners, deadlines — and
delivers it by email, with zero data ever leaving the internal network.

## User
Medpark hospital executive, administrative, and medical board leadership.
Real pain: meeting decisions get lost or misremembered; existing transcription
tools are cloud-based, which violates medical data policy, and none of them
handle Romanian/Russian/English code-switching plus medical vocabulary well.

## MVP (build this first, nothing else)
Upload ONE pre-recorded hospital meeting →
local transcription →
local LLM extracts decisions / owners / deadlines →
generate a MoM document →
send it through local SMTP (Mailpit).
No live recording. No diarization. No auth. No polish.

## Architecture
```
   WEB UI (upload + meeting type)
            |
        FastAPI
            |
  +---------+----------+
  |                     |
 ASR                Meeting type
(faster-whisper)        |
  |                     |
transcript               |
  |                      |
Local LLM (Ollama) ------+
  |
structured JSON (decisions/owners/deadlines)
  |
MoM generator (Markdown)
  |
Local SMTP (Mailpit)
  |
Email delivered
```
Every stage is a pure function: input in, structured data out. No stage
calls anything outside localhost.

## Dev 1 → Dev 2 contract
ASR returns a transcript object with `text`, `detected_language`, and
`segments`. The current FastAPI integration passes `transcript["text"]` to
`extract_decisions(transcript: str)`. Extraction returns `meeting_summary`
and `action_items`; each item has `decision`, `owner`, and `deadline`, with
missing owners or deadlines represented as `null`. Optional `evidence` and
`confidence` fields support review and evaluation. The LLM response is
validated against `backend/schemas.py` before it reaches MoM generation.

## Tech stack
- Backend: Python 3.11, FastAPI, uvicorn
- ASR: faster-whisper (runs local, CPU or GPU)
- LLM: Ollama running locally (mistral or phi3), called over localhost HTTP
- Email: local SMTP via Mailpit (docker), stdlib smtplib
- Frontend: one static HTML file, no build step, no CDN dependencies (must
  work with the network cable pulled out)

## Constraints
- 100% offline at inference time. Zero calls to any non-localhost host when
  actually processing a meeting. This is a hard pass/fail judging gate —
  the jury may physically disconnect the network during the demo.
- Target hardware: 16 GB GPU, OR CPU-only with 32 GB RAM. Don't pick a model
  that needs more than that.
- Target speed: under 15 minutes end-to-end for a 60-minute recording.
- Romanian / Russian / English code-switching within a single sentence, plus
  medical terminology, is the actual hard problem — not the UI, not email.

## Current state
Scaffold only. Nothing has been run against real audio yet.
<!-- update this section as you go: what works, what's stubbed, what's next -->

## Known bugs
<!-- update as you find them -->

## Do NOT
- Do NOT call any cloud API (OpenAI, Anthropic, Google, AWS, Gmail/Outlook
  SMTP, SendGrid, etc.) at runtime — instant disqualification.
- Do NOT start with live microphone capture. Batch upload only, for the MVP.
- Do NOT build speaker diarization before the core pipeline works end-to-end.
- Do NOT let the AI rewrite unrelated files when debugging one stage.
- Do NOT spend hours on the frontend before the pipeline produces a correct
  MoM from at least one real sample recording.

## Coding conventions
- Every pipeline stage lives in its own `backend/*.py` module and is callable
  standalone (see `scripts/smoke_test.py`) — not just from inside a FastAPI
  request handler.
- Config comes from environment variables (`backend/config.py`), never
  hardcoded model names or hosts.
- Errors are raised, not swallowed. If a stage fails, the API call should
  fail loudly, not return an empty MoM.
