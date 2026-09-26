"""
All environment configuration lives here — nowhere else in the codebase
should call os.environ directly. Makes it obvious, at a glance, that
nothing is hardcoded to a cloud host.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Email / routing
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
MOM_RECIPIENTS = [
    addr.strip()
    for addr in os.getenv("MOM_RECIPIENTS", "board@medpark.local").split(",")
    if addr.strip()
]

# ASR
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "medium")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

# Local LLM
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

# Storage
DATA_DIR = os.getenv("DATA_DIR", "./data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
OUTPUT_DIR = os.path.join(DATA_DIR, "output")
