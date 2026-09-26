# Secure MOM

On-premise pipeline that turns a hospital meeting recording into a structured
Minutes of Meeting — decisions, owners, deadlines — and emails it out,
without any audio, transcript, or decision data ever leaving the local
network.

Built for the Medpark HealthTech challenge at DeepTech GigaHack 2026.

## How it works

```
audio file
   -> faster-whisper (local ASR)          -> transcript
   -> Ollama / local LLM                  -> decisions, owners, deadlines
   -> MoM generator                       -> Markdown document
   -> local SMTP (Mailpit)                -> email delivered
```

Everything above the line runs on localhost. Nothing calls out to the
internet while processing a meeting — that's the whole point of the
challenge, and it's judged pass/fail.

## Quickstart

### 1. Install Python deps
```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start a local LLM (Ollama)
```bash
# install from https://ollama.com if you don't have it yet
ollama pull mistral        # or phi3 — pick whichever fits your RAM/GPU
ollama serve                # usually already running as a service
```

### 3. Start local SMTP capture (Mailpit)
```bash
docker compose up -d mailpit
# Web UI to see captured emails: http://localhost:8025
```
No Docker? Any local mail-catcher works — set `SMTP_HOST` / `SMTP_PORT` in
`.env` to match.

### 4. Configure
```bash
cp .env.example .env
# edit .env if your model names / ports differ from the defaults
```

### 5. Run the app
```bash
uvicorn backend.main:app --reload --port 8000
```
Open http://localhost:8000 — upload a recording, pick a meeting type, hit
Run. The generated MoM will show on the page and land in Mailpit
(http://localhost:8025).

### 6. Sanity-check the pipeline without the web UI
```bash
python scripts/smoke_test.py data/samples/<a-sample-file>.wav
```
This runs ASR -> extraction -> MoM generation and prints each stage's
output, so you can tell which stage is wrong when something breaks.

### 7. Run the Dev 2 contract tests
```bash
python -m unittest discover -s tests
```
These tests validate extraction schema/parsing and MoM formatting without
requiring Ollama or hospital audio. The multilingual transcript fixture is
in `tests/fixtures/sample_transcript.txt`; use an approved real ASR transcript
for model-quality evaluation when one is available.

## Project layout
```
secure-mom/
├── PROJECT.md              context file — paste into any AI coding session
├── README.md                this file
├── backend/
│   ├── main.py               FastAPI app + the one /api/process endpoint
│   ├── config.py              env var loading, all in one place
│   ├── schemas.py             pydantic models (ActionItem, MoMResult, ...)
│   ├── asr.py                  faster-whisper wrapper
│   ├── llm_extract.py          Ollama call + prompt + JSON parsing/validation
│   ├── mom_generator.py        turns structured data into a MoM document
│   └── mailer.py               sends the MoM over local SMTP
├── frontend/
│   └── index.html              single-file upload UI, no build step
├── prompts/
│   └── extraction_prompt.md    the LLM prompt, kept separate so you can
│                                iterate on it without touching Python
├── scripts/
│   └── smoke_test.py           run the pipeline on one file from the CLI
├── tests/
│   ├── test_dev2.py             extraction contract and MoM tests
│   └── fixtures/
│       └── sample_transcript.txt multilingual development fixture
└── data/
    ├── samples/                 put the GigaHack-provided test recordings here
    ├── uploads/                  runtime uploads land here (gitignored)
    └── output/                   generated MoM files land here (gitignored)
```

## What to build first (see PROJECT.md → MVP)
1. Get `scripts/smoke_test.py` producing a real transcript from one sample
   recording. That alone proves ASR works on this machine.
2. Get the LLM extraction step returning valid JSON for that transcript —
   this is the part worth the most judging points, so don't rush it.
3. Wire the two together behind the FastAPI endpoint.
4. Only then: email delivery, then the frontend polish.

## Known limitations (be upfront about these in the pitch)
- faster-whisper is given a single `language` setting per call; true
  sentence-level code-switching (Romanian → English medical term → Russian
  mid-sentence) is the hardest part of this challenge and the baseline here
  does not solve it — that's the highest-value thing to improve during the
  hackathon (see `backend/asr.py` for where to start).
- No speaker diarization in the MVP (explicitly a bonus in the brief, not a
  requirement).
- No authentication — this is a hackathon prototype, not a production
  deployment.

## Offline check before the demo
Before you present, pull the network cable (or disable Wi-Fi) and run the
full pipeline once. If it still works, you pass the Security & Architecture
gate. If anything hangs or errors, something is still calling out — check
`backend/llm_extract.py` and `backend/asr.py` for a stray URL.
