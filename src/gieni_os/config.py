"""
Gieni OS Configuration Module
Environment keys, database UUIDs, thresholds, and operational constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(REPO_ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/gieni_os.db")

NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_VERSION = "2022-06-28"

KB_DB_ID = os.environ.setdefault("NOTION_KB_DB_ID", "3e0b5bd1-d90c-812c-9c65-d25cefd633a3")
CLIENTS_DB_ID = os.environ.setdefault("NOTION_CLIENTS_DB_ID", "3e0b5bd1-d90c-810e-a326-de5677c60e18")
OPPORTUNITIES_DB_ID = os.environ.setdefault("NOTION_OPPORTUNITIES_DB_ID", "3e0b5bd1-d90c-81e6-bb4d-c1bc60166a40")
COUNTIES_DB_ID = os.environ.setdefault("NOTION_COUNTIES_DB_ID", "3e0b5bd1-d90c-8105-b6fd-ef9a8371d96b")
PIERCE_COUNTY_PAGE_ID = os.environ.setdefault("NOTION_PIERCE_COUNTY_PAGE_ID", "3e0b5bd1-d90c-814d-af6a-d971b052115d")

# Operational Thresholds
PAS_DELIVERY_THRESHOLD = 70.0
NET_EQUITY_MIN_THRESHOLD = 50000.0
QC_CONFIDENCE_THRESHOLD = 85.0
QC_HITL_THRESHOLD = 60.0

PRIORITY_A_THRESHOLD = 85
PRIORITY_B_THRESHOLD = 65

# Security Encryption Key (for at-rest storage)
AES_SECRET_KEY = os.getenv("AES_SECRET_KEY")
if not AES_SECRET_KEY:
    raise RuntimeError("AES_SECRET_KEY environment variable is unset. Production encryption requires an explicit secret key.")

# Message Bus & Cache
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# LLM Gateway Settings: Azure OpenAI & Ollama
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip()
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o").strip()
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview").strip()

raw_ollama_host = os.getenv("OLLAMA_HOST") or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434"
raw_ollama_host = raw_ollama_host.strip().rstrip("/")
if not raw_ollama_host.startswith("http://") and not raw_ollama_host.startswith("https://"):
    raw_ollama_host = f"http://{raw_ollama_host}"
OLLAMA_HOST = raw_ollama_host

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b").strip()
LLM_PROVIDER_OVERRIDE = os.getenv("LLM_PROVIDER_OVERRIDE", "").strip().upper()

# Skip-Trace & Legal Contact Enrichment Settings
SKIP_TRACE_PROVIDER = os.getenv("SKIP_TRACE_PROVIDER", "MANUAL").strip().upper()  # BATCH_DATA | TRACERS | IDI_CORE | MANUAL
SKIP_TRACE_API_KEY = os.getenv("SKIP_TRACE_API_KEY", "").strip()
SKIP_TRACE_ENDPOINT = os.getenv("SKIP_TRACE_ENDPOINT", "").strip()


def validate_environment(example_path: Path = REPO_ROOT / ".env.example") -> list[str]:
    """
    Validate that all non-commented keys present in .env.example are defined in os.environ.
    Raises RuntimeError if any required keys are missing.
    """
    if not example_path.exists():
        return []
    required_keys = []
    with open(example_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key = line.split("=", 1)[0].strip()
                if key:
                    required_keys.append(key)
    missing = [k for k in required_keys if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing required environment variables defined in .env.example: {missing}")
    return required_keys

# Run environment validation at configuration load
validate_environment()


