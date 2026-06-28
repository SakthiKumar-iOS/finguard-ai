# config/settings.py
# Purpose: Load and expose configuration settings from environment variables.

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Project root directory for resolving absolute paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Env variables exposure
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("MCP_PORT", "8765"))

# Helper for boolean values
def _to_bool(val: str, default: bool) -> bool:
    if val is None:
        return default
    return val.lower() in ("true", "1", "t", "y", "yes")

PII_REDACTION_ENABLED = _to_bool(os.getenv("PII_REDACTION_ENABLED"), True)
PROMPT_INJECTION_GUARD = _to_bool(os.getenv("PROMPT_INJECTION_GUARD"), True)
LOCAL_ONLY_MODE = _to_bool(os.getenv("LOCAL_ONLY_MODE"), True)

# Absolute paths
def _get_abs_path(env_key: str, default_rel_path: str) -> str:
    path_val = os.getenv(env_key)
    if not path_val:
        return str((PROJECT_ROOT / default_rel_path).resolve())
    path_obj = Path(path_val)
    if path_obj.is_absolute():
        return str(path_obj.resolve())
    return str((PROJECT_ROOT / path_obj).resolve())

TRANSACTIONS_FILE = _get_abs_path("TRANSACTIONS_FILE", "data/transactions/mock_transactions.json")
PRODUCTS_FILE = _get_abs_path("PRODUCTS_FILE", "data/knowledge_base/products.json")
AUDIT_LOG_DIR = _get_abs_path("AUDIT_LOG_DIR", "data/audit_logs")

if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
    raise RuntimeError(
        "GEMINI_API_KEY is missing.\n"
        "Run: cp .env.example .env\n"
        "Then add your key from: https://aistudio.google.com/app/apikey"
    )

