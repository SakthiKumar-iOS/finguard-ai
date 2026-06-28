# utils/logger.py
# Purpose: Handle audit and system logging utilities.

import logging
import os
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path
from config.settings import AUDIT_LOG_DIR

# Ensure directory is created
try:
    os.makedirs(AUDIT_LOG_DIR, exist_ok=True)
except Exception:
    pass

# Create module-level logger
logger = logging.getLogger("finguard")
logger.setLevel(logging.DEBUG)
logger.propagate = False  # Avoid duplicate logs if root logger is active

# Setup formats
file_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(module)s | %(message)s")
console_formatter = logging.Formatter("%(levelname)s | %(message)s")

# File Handler
log_file_path = Path(AUDIT_LOG_DIR) / "finguard.log"
try:
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=1 * 1024 * 1024,  # 1MB
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
except Exception as e:
    # Fallback to console only if file handler fails (e.g. permission error)
    pass

# Console Handler (WARNING and above)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Allowed lists
ALLOWED_INTENTS = {"transaction", "product", "eligibility", "service", "audit", "unknown", "blocked"}
ALLOWED_STATUSES = {"clean", "redacted", "blocked", "success", "failed", "unavailable"}
ALLOWED_EVENTS = {
    "pii_detected", "injection_attempt", "jailbreak_attempt",
    "invalid_input", "blocked_request", "validation_failed"
}

# Regex patterns for PII stripping in log details
RE_10_DIGIT = re.compile(r"\b\d{10,}\b")
RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
RE_CARD = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")

# Metadata sanitization keys
STRIP_METADATA_KEYS = {
    "key", "token", "password", "secret", "account", "card", "ssn", "dob",
    "phone", "email", "name", "address"
}

def log_intent(intent: str, status: str, metadata: dict = None) -> None:
    """Log intent and status to the finguard logger if valid."""
    if metadata is None:
        metadata = {}

    if intent not in ALLOWED_INTENTS or status not in ALLOWED_STATUSES:
        logger.warning("Invalid log entry rejected")
        return

    # Sanitize metadata
    sanitized = {}
    for k, v in metadata.items():
        k_lower = k.lower()
        if not any(strip_key in k_lower for strip_key in STRIP_METADATA_KEYS):
            sanitized[k] = v

    logger.info(f"INTENT={intent} STATUS={status} META={sanitized}")

def log_security_event(event_type: str, details: str = "") -> None:
    """Log security events to the finguard logger, stripping any PII from details."""
    if event_type not in ALLOWED_EVENTS:
        logger.warning(f"Invalid security event type rejected: {event_type}")
        return

    # Max 100 characters for details
    details_str = str(details or "")[:100]

    # Strip PII patterns from details
    details_str = RE_10_DIGIT.sub("[REDACTED_NUM]", details_str)
    details_str = RE_EMAIL.sub("[REDACTED_EMAIL]", details_str)
    details_str = RE_CARD.sub("[REDACTED_CARD]", details_str)

    logger.warning(f"SECURITY_EVENT={event_type} DETAILS={details_str}")

def log_error(module: str, error_type: str) -> None:
    """Log an error under the given module and error type (exceptions only)."""
    logger.error(f"MODULE={module} ERROR={error_type}")

def get_logger() -> logging.Logger:
    """Return the module-level logger."""
    return logger
