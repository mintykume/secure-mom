"""
Run the pipeline against one audio file from the command line, printing
each stage's output. Use this to find out which stage is broken instead of
debugging through the web UI.

Usage:
    python scripts/smoke_test.py data/samples/<file>.wav
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.asr import transcribe_audio
from backend.llm_extract import extract_decisions
from backend.mom_generator import generate_mom_markdown


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    audio_path = sys.argv[1]

    print(f"\n== 1/3 Transcribing {audio_path} ==")
    transcript = transcribe_audio(audio_path)
    print(f"Detected language: {transcript['detected_language']}")
    print(f"Transcript ({len(transcript['text'])} chars):\n{transcript['text'][:1000]}")

    print("\n== 2/3 Extracting decisions (local LLM) ==")
    extraction = extract_decisions(transcript["text"])
    print(json.dumps(extraction, indent=2, ensure_ascii=False))

    print("\n== 3/3 Generating MoM ==")
    mom = generate_mom_markdown(
        meeting_type="medical",
        meeting_id="smoke-test",
        extraction=extraction,
        detected_language=transcript["detected_language"],
        transcript_excerpt=transcript["text"],
    )
    print(mom)


if __name__ == "__main__":
    main()
