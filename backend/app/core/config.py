import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / '.env')
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_TEXT_CHARS = 40000
MAX_JOB_CHARS = 16000
MAX_LLM_CHARS = 20000
MAX_CANDIDATES = 5
MODEL_DIR = ROOT / 'models'


def allowed_origins() -> list[str]:
    return os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')
