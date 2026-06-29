# utils/prompt_guard.py
# Purpose: Guard against prompt injection and malicious inputs.

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

_MAX_INPUT_LENGTH = 2000

# ---------------------------------------------------------------------------
# Injection / jailbreak patterns (case-insensitive)
# ---------------------------------------------------------------------------
_INJECTION_PATTERNS: list[tuple[str, str]] = [
    ("ignore previous instructions", "prompt_injection"),
    ("ignore all instructions", "prompt_injection"),
    ("disregard your", "prompt_injection"),
    ("forget your instructions", "prompt_injection"),
    ("override your", "prompt_injection"),
    ("you are now", "jailbreak"),
    ("act as", "jailbreak"),
    ("pretend you are", "jailbreak"),
    ("roleplay as", "jailbreak"),
    ("simulate being", "jailbreak"),
    ("bypass", "jailbreak"),
    ("jailbreak", "jailbreak"),
    ("do anything now", "jailbreak"),
    ("dan mode", "jailbreak"),
    ("developer mode", "jailbreak"),
    ("unrestricted mode", "jailbreak"),
    ("ignore your training", "prompt_injection"),
    ("ignore safety", "prompt_injection"),
    ("disable filters", "prompt_injection"),
    ("reveal your prompt", "prompt_injection"),
    ("show your instructions", "prompt_injection"),
    ("what are your instructions", "prompt_injection"),
    ("ignore compliance", "prompt_injection"),
    ("ignore regulations", "prompt_injection"),
]

# ---------------------------------------------------------------------------
# Banking-specific abuse patterns
# ---------------------------------------------------------------------------
_BANKING_ABUSE_PATTERNS: list[tuple[str, str]] = [
    ("transfer all funds", "banking_abuse"),
    ("send money to", "banking_abuse"),
    ("wire transfer", "banking_abuse"),
    ("share account details", "banking_abuse"),
    ("reveal account", "banking_abuse"),
    ("expose customer", "banking_abuse"),
    ("bypass kyc", "banking_abuse"),
    ("bypass aml", "banking_abuse"),
    ("launder", "banking_abuse"),
    ("circumvent", "banking_abuse"),
]

# Pre-compile all patterns for efficiency
_COMPILED_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (re.compile(re.escape(pattern), re.IGNORECASE), pattern, threat_type)
    for pattern, threat_type in (_INJECTION_PATTERNS + _BANKING_ABUSE_PATTERNS)
]

_SECURITY_BYPASS_KEYWORDS = [
    "override", "bypass", "jailbreak", "disable", "unrestricted", "circumvent",
    "manipulate", "exploit", "hack", "crack", "intercept", "infiltrate",
    "hijack", "spoof", "tamper", "sabotage", "subvert", "deceive", "impersonate",
    "masquerade"
]

_INSTRUCTION_OVERRIDE_KEYWORDS = [
    "disobey", "disregard", "overrule", "nullify", "cancel instructions",
    "reset instructions", "new instructions", "updated instructions", "ignore rules",
    "break rules", "no rules", "without rules", "unrestricted access", "full access",
    "admin access", "root access", "superuser", "god mode", "debug mode", "test mode",
    "maintenance mode"
]

_DATA_ABUSE_KEYWORDS = [
    "steal", "exfiltrate", "extract all", "dump", "scrape", "harvest", "mine data",
    "leak", "expose all", "print all", "export all", "download all", "copy all",
    "share all", "send all", "unauthorised", "unauthorized", "without permission",
    "without authorisation", "without consent"
]

_FINANCIAL_FRAUD_KEYWORDS = [
    "fraudulent", "illicit", "illegal transfer", "fake transaction", "forge",
    "falsify", "manipulate balance", "alter transaction", "modify record",
    "delete record", "wipe record", "clear history", "erase log", "hide transaction",
    "conceal", "wash funds", "smurfing", "structuring", "front company", "shell account"
]

_SOCIAL_ENGINEERING_KEYWORDS = [
    "trust me", "i am the admin", "i am a developer", "i am authorized",
    "i have permission", "i am the owner", "emergency override", "urgent override",
    "special access", "privileged access", "internal access", "staff mode",
    "employee mode", "support mode", "system prompt", "master prompt", "base prompt",
    "hidden prompt", "secret prompt", "original prompt"
]

_SYSTEM_PROBING_KEYWORDS = [
    "what is your system", "show your config", "print your config", "show your code",
    "print your code", "list your agents", "show your agents", "what agents",
    "internal architecture", "show database", "access database", "show file",
    "read file", "list files", "directory listing", "file path", "system path",
    "environment variable", "show env", "print env"
]

_NEW_KEYWORD_GROUPS = [
    ("security_bypass_attempt", _SECURITY_BYPASS_KEYWORDS),
    ("instruction_override_attempt", _INSTRUCTION_OVERRIDE_KEYWORDS),
    ("data_abuse_attempt", _DATA_ABUSE_KEYWORDS),
    ("financial_fraud_attempt", _FINANCIAL_FRAUD_KEYWORDS),
    ("social_engineering_attempt", _SOCIAL_ENGINEERING_KEYWORDS),
    ("system_probe_attempt", _SYSTEM_PROBING_KEYWORDS),
]


def scan(text: str) -> dict:
    """Scan *text* for prompt injection and banking-abuse patterns.

    Returns:
        {
            "is_safe": bool,
            "threat_type": str or None,
            "threat_pattern": str or None,
            "action": "block" or "allow"
        }

    Handles None, empty string, and non-string input gracefully.
    Input is silently truncated at 2000 characters.
    Never logs or echoes the original unsafe input.
    """
    # --- Input validation ---
    if text is None or not isinstance(text, str):
        return {
            "is_safe": True,
            "threat_type": None,
            "threat_pattern": None,
            "action": "allow",
        }

    if text.strip() == "":
        return {
            "is_safe": True,
            "threat_type": None,
            "threat_pattern": None,
            "action": "allow",
        }

    # --- Truncate silently ---
    was_truncated = len(text) > _MAX_INPUT_LENGTH
    scanned_text = text[:_MAX_INPUT_LENGTH]

    # --- Pattern matching (exact phrases) ---
    for compiled, raw_pattern, threat_type in _COMPILED_PATTERNS:
        if compiled.search(scanned_text):
            # Log threat type only — never log the original text
            logger.warning(
                "Threat detected: threat_type=%s was_truncated=%s",
                threat_type,
                was_truncated,
            )
            return {
                "is_safe": False,
                "threat_type": threat_type,
                "threat_pattern": raw_pattern,
                "action": "block",
            }

    # --- Keyword group matching (individual keyword matching) ---
    scanned_text_lower = scanned_text.lower()
    for threat_type, keywords_list in _NEW_KEYWORD_GROUPS:
        for kw_phrase in keywords_list:
            words = kw_phrase.lower().split()
            if all(w in scanned_text_lower for w in words):
                logger.warning(
                    "Threat detected: threat_type=%s was_truncated=%s",
                    threat_type,
                    was_truncated,
                )
                return {
                    "is_safe": False,
                    "threat_type": threat_type,
                    "threat_pattern": kw_phrase,
                    "action": "block",
                }

    return {
        "is_safe": True,
        "threat_type": None,
        "threat_pattern": None,
        "action": "allow",
    }
