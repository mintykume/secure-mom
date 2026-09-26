"""
Local speech-to-text via faster-whisper. Runs fully offline once the model
weights are downloaded once (during setup, before the demo).

--- THE HARD PART OF THIS CHALLENGE LIVES HERE ---
faster-whisper picks ONE language per call by default. Real hospital
meetings here code-switch mid-sentence: Romanian grammar, an English
medical term, a sentence in Russian, back to Romanian. A naive single-
language transcription will mangle two of the three languages.

Baseline in this file: transcribe once with language=None (auto-detect)
and vad_filter on, which at least lets faster-whisper vary its guess
segment-to-segment instead of locking to one language for the whole file.

Highest-value next step (do this before polishing anything else):
  - Inspect segments where confidence is low or the detected language
    flips — those are your code-switch boundaries.
  - Consider re-running short low-confidence segments with each candidate
    language explicitly set (ro / ru / en) and keeping whichever
    transcription has the higher avg_logprob.
  - A domain glossary (hotword list) for medical terms is supported by
    faster-whisper via the `hotwords` argument — worth populating from the
    sample transcripts once you've listened to them.
"""
from functools import lru_cache
from faster_whisper import WhisperModel

from . import config


@lru_cache(maxsize=1)
def get_model() -> WhisperModel:
    return WhisperModel(
        config.WHISPER_MODEL_SIZE,
        device=config.WHISPER_DEVICE,
        compute_type=config.WHISPER_COMPUTE_TYPE,
    )


def transcribe_audio(path: str) -> dict:
    """Returns {"text": str, "detected_language": str, "segments": [...]}"""
    model = get_model()
    segments, info = model.transcribe(
        path,
        beam_size=5,
        vad_filter=True,
        language=None,  # auto-detect per call; see module docstring
    )

    seg_list = []
    text_parts = []
    for seg in segments:
        text_parts.append(seg.text.strip())
        seg_list.append(
            {
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip(),
                "avg_logprob": round(seg.avg_logprob, 3),
            }
        )

    return {
        "text": " ".join(text_parts).strip(),
        "detected_language": info.language,
        "segments": seg_list,
    }
