# utils/pii_redactor.py
# Purpose: Redact sensitive PII from text inputs using Microsoft Presidio.

import logging
import re
from typing import Optional

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Supported Presidio entity types
# ---------------------------------------------------------------------------
_PRESIDIO_ENTITIES = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD",
    "IBAN_CODE",
    "US_SSN",
    "US_BANK_NUMBER",
    "LOCATION",
    "DATE_TIME",
    "URL",
    "IP_ADDRESS",
    "NRP",
]

# ---------------------------------------------------------------------------
# Custom regex-based recognizers
# ---------------------------------------------------------------------------

def _build_account_number_recognizer() -> PatternRecognizer:
    """10–16 consecutive digit sequences (account numbers)."""
    pattern = Pattern(
        name="account_number_pattern",
        regex=r"\b\d{10,16}\b",
        score=0.85,
    )
    return PatternRecognizer(
        supported_entity="ACCOUNT_NUMBER",
        patterns=[pattern],
        name="AccountNumberRecognizer",
    )


def _build_card_number_recognizer() -> PatternRecognizer:
    """13–19 digit card numbers with optional dashes or spaces."""
    pattern = Pattern(
        name="card_number_pattern",
        regex=r"\b(?:\d[ -]?){12,18}\d\b",
        score=0.85,
    )
    return PatternRecognizer(
        supported_entity="CARD_NUMBER",
        patterns=[pattern],
        name="CardNumberRecognizer",
    )


def _build_bsb_recognizer() -> PatternRecognizer:
    """Australian BSB: 6 digits with optional dash (e.g. 123-456)."""
    pattern = Pattern(
        name="bsb_pattern",
        regex=r"\b\d{3}-?\d{3}\b",
        score=0.75,
    )
    return PatternRecognizer(
        supported_entity="BSB_NUMBER",
        patterns=[pattern],
        name="BSBRecognizer",
    )


def _build_otp_pin_recognizer() -> PatternRecognizer:
    """OTP / PIN: 4–8 standalone consecutive digits."""
    pattern = Pattern(
        name="otp_pin_pattern",
        regex=r"(?<!\d)\d{4,8}(?!\d)",
        score=0.6,
    )
    return PatternRecognizer(
        supported_entity="OTP_PIN",
        patterns=[pattern],
        name="OTPPinRecognizer",
    )


# ---------------------------------------------------------------------------
# Engine initialisation (module-level singleton — read-only after init)
# ---------------------------------------------------------------------------

def _build_analyzer() -> AnalyzerEngine:
    """Build and return a configured AnalyzerEngine."""
    # Use spaCy en_core_web_sm as the NLP engine
    provider = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
    })
    nlp_engine = provider.create_engine()

    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])

    # Register custom recognizers
    analyzer.registry.add_recognizer(_build_account_number_recognizer())
    analyzer.registry.add_recognizer(_build_card_number_recognizer())
    analyzer.registry.add_recognizer(_build_bsb_recognizer())
    analyzer.registry.add_recognizer(_build_otp_pin_recognizer())

    return analyzer


_analyzer: Optional[AnalyzerEngine] = None
_anonymizer: Optional[AnonymizerEngine] = None


def _get_engines():
    """Lazy-initialise the Presidio engines (thread-safe at module import)."""
    global _analyzer, _anonymizer
    if _analyzer is None:
        _analyzer = _build_analyzer()
    if _anonymizer is None:
        _anonymizer = AnonymizerEngine()
    return _analyzer, _anonymizer


# ---------------------------------------------------------------------------
# All entity types we want to detect (Presidio built-ins + custom)
# ---------------------------------------------------------------------------
_ALL_ENTITIES = _PRESIDIO_ENTITIES + [
    "ACCOUNT_NUMBER",
    "CARD_NUMBER",
    "BSB_NUMBER",
    "OTP_PIN",
]


def redact(text: str) -> dict:
    """Detect and redact PII from *text*.

    Returns:
        {
            "redacted": str,          # text with PII replaced
            "found_entities": list,   # list of entity-type strings detected
            "is_safe": bool           # True only when found_entities is empty
        }

    Handles None, empty string, and non-string inputs gracefully.
    Never logs original PII values — only entity types and character positions.
    """
    # --- Input validation ---
    if text is None or not isinstance(text, str):
        return {"redacted": "", "found_entities": [], "is_safe": True}

    if text.strip() == "":
        return {"redacted": text, "found_entities": [], "is_safe": True}

    analyzer, anonymizer = _get_engines()

    # --- Analyse ---
    results = analyzer.analyze(text=text, language="en", entities=_ALL_ENTITIES)

    # Log entity type + position only (never the value)
    for r in results:
        logger.debug(
            "PII detected: entity_type=%s start=%d end=%d score=%.2f",
            r.entity_type,
            r.start,
            r.end,
            r.score,
        )

    found_entities = [r.entity_type for r in results]

    if not results:
        return {"redacted": text, "found_entities": [], "is_safe": True}

    # --- Anonymize — replace with [REDACTED_<ENTITY_TYPE>] ---
    operators = {
        entity: OperatorConfig(
            "replace", {"new_value": f"[REDACTED_{entity}]"}
        )
        for entity in _ALL_ENTITIES
    }

    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators=operators,
    )

    return {
        "redacted": anonymized.text,
        "found_entities": found_entities,
        "is_safe": False,
    }
