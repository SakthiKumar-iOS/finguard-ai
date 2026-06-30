# agents/session_validator_adk.py
# Purpose: ADK-based session validator. Runs once at startup to confirm all
# security and data dependencies are ready before the multi-agent system
# accepts user input.

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Graceful ADK import — fail clearly if package is missing
try:
    from google.adk.agents import Agent as _ADKAgent  # type: ignore
    _ADK_AVAILABLE = True
except ImportError:
    _ADKAgent = object  # fallback base so class definition still works
    _ADK_AVAILABLE = False


class SessionValidatorAgent(_ADKAgent):
    """ADK-based session validator. Runs once at startup to confirm all
    security and data dependencies are ready before the multi-agent system
    accepts user input."""

    # ADK agent metadata
    name: str = "session_validator"
    description: str = (
        "Validates the local session is ready before chat starts. "
        "Performs 7 deterministic checks — no LLM call required."
    )

    def __init__(self):
        if not _ADK_AVAILABLE:
            # Skip ADK Agent __init__ and store availability flag
            self._adk_missing = True
        else:
            try:
                super().__init__(
                    name=self.name,
                    description=self.description,
                    model="",          # no model — deterministic agent
                    instruction="",    # no LLM instruction needed
                )
            except Exception:
                pass
            self._adk_missing = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _project_root() -> Path:
        """Return the project root directory (two levels up from this file)."""
        return Path(__file__).resolve().parent.parent

    def _check_gemini_api_key(self) -> str | None:
        """Check 1: GEMINI_API_KEY is present and not placeholder."""
        try:
            key = os.getenv("GEMINI_API_KEY", "")
            if not key or key.strip() == "your_gemini_api_key_here":
                return "GEMINI_API_KEY is missing or still set to placeholder value"
            return None
        except Exception as exc:
            return f"GEMINI_API_KEY check error: {exc}"

    def _check_audit_log_dir(self) -> str | None:
        """Check 2: AUDIT_LOG_DIR exists and is writable."""
        try:
            raw = os.getenv("AUDIT_LOG_DIR", "data/audit_logs")
            path = Path(raw) if Path(raw).is_absolute() else self._project_root() / raw
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
            if not os.access(path, os.W_OK):
                return f"AUDIT_LOG_DIR is not writable: {path}"
            return None
        except Exception as exc:
            return f"AUDIT_LOG_DIR check error: {exc}"

    def _check_transactions_file(self) -> str | None:
        """Check 3: TRANSACTIONS_FILE exists and is readable."""
        try:
            raw = os.getenv(
                "TRANSACTIONS_FILE",
                "data/transactions/mock_transactions.json",
            )
            path = Path(raw) if Path(raw).is_absolute() else self._project_root() / raw
            if not path.exists():
                return f"TRANSACTIONS_FILE not found: {path}"
            if not os.access(path, os.R_OK):
                return f"TRANSACTIONS_FILE is not readable: {path}"
            return None
        except Exception as exc:
            return f"TRANSACTIONS_FILE check error: {exc}"

    def _check_products_file(self) -> str | None:
        """Check 4: PRODUCTS_FILE exists and is readable."""
        try:
            raw = os.getenv(
                "PRODUCTS_FILE",
                "data/knowledge_base/products.json",
            )
            path = Path(raw) if Path(raw).is_absolute() else self._project_root() / raw
            if not path.exists():
                return f"PRODUCTS_FILE not found: {path}"
            if not os.access(path, os.R_OK):
                return f"PRODUCTS_FILE is not readable: {path}"
            return None
        except Exception as exc:
            return f"PRODUCTS_FILE check error: {exc}"

    def _check_pii_redaction(self) -> str | None:
        """Check 5: PII_REDACTION_ENABLED is true."""
        try:
            val = os.getenv("PII_REDACTION_ENABLED", "true").lower()
            if val not in ("true", "1", "t", "y", "yes"):
                return "PII_REDACTION_ENABLED is not set to true — required for security compliance"
            return None
        except Exception as exc:
            return f"PII_REDACTION_ENABLED check error: {exc}"

    def _check_prompt_injection_guard(self) -> str | None:
        """Check 6: PROMPT_INJECTION_GUARD is true."""
        try:
            val = os.getenv("PROMPT_INJECTION_GUARD", "true").lower()
            if val not in ("true", "1", "t", "y", "yes"):
                return "PROMPT_INJECTION_GUARD is not set to true — required for security compliance"
            return None
        except Exception as exc:
            return f"PROMPT_INJECTION_GUARD check error: {exc}"

    def _check_local_only_mode(self) -> str | None:
        """Check 7: LOCAL_ONLY_MODE is true."""
        try:
            val = os.getenv("LOCAL_ONLY_MODE", "true").lower()
            if val not in ("true", "1", "t", "y", "yes"):
                return "LOCAL_ONLY_MODE is not set to true — data should not leave local environment"
            return None
        except Exception as exc:
            return f"LOCAL_ONLY_MODE check error: {exc}"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(self) -> dict:
        """Run all 7 startup checks and return a readiness report.

        Returns:
            {
                "ready": bool,
                "checks_passed": int,
                "checks_total": 7,
                "issues": list[str]  # empty when ready=True
            }
        """
        if self._adk_missing:
            return {
                "ready": False,
                "checks_passed": 0,
                "checks_total": 7,
                "issues": [
                    "google-adk package is not installed. "
                    "Run: pip install google-adk"
                ],
            }

        checks = [
            self._check_gemini_api_key,
            self._check_audit_log_dir,
            self._check_transactions_file,
            self._check_products_file,
            self._check_pii_redaction,
            self._check_prompt_injection_guard,
            self._check_local_only_mode,
        ]

        issues: list[str] = []
        for check_fn in checks:
            issue = check_fn()
            if issue is not None:
                issues.append(issue)

        checks_passed = len(checks) - len(issues)
        return {
            "ready": len(issues) == 0,
            "checks_passed": checks_passed,
            "checks_total": 7,
            "issues": issues,
        }
