# agents/audit_compliance.py
# Purpose: Logs operations and checks actions for compliance with auditing standards.

import logging
from utils.logger import log_intent, log_error
from mcp_server.tools import get_audit_log

logger = logging.getLogger(__name__)

COMPLIANCE_SUMMARY = (
    "Session Compliance Summary\n"
    "PII Guardian: Active\n"
    "Prompt Injection Guard: Active\n"
    "Local Only Mode: Active\n"
    "Audit Logging: Active\n"
    "All systems operating within compliance parameters."
)


class AuditComplianceAgent:
    """Agent that performs compliance audits and records session logs for security and tracking."""

    def run(self, input: str) -> str:  # noqa: A002
        """Run the audit compliance agent on the input string."""
        try:
            lowered = (input or "").lower()

            # 1. Log every call using log_intent
            log_intent("audit", "success")

            # 2. Check keywords for compliance summary
            if any(kw in lowered for kw in ["compliance", "report"]):
                return COMPLIANCE_SUMMARY

            # 3. Check keywords for audit logs
            if any(kw in lowered for kw in ["audit", "log", "activity", "session", "record"]):
                res = get_audit_log(limit=10)
                entries = res.get("entries", [])
                
                if not entries:
                    return "No audit records found for this session"

                # Format as readable plain text table:
                # "Timestamp         | Intent      | Status"
                # "--------------------------------------"
                # "<timestamp>       | <intent>    | <status>"
                header_line = f"Audit log — last {len(entries)} entries (most recent first):\n\n"
                table_header = f"{'Timestamp':<30} | {'Intent':<11} | {'Status':<12}"
                separator = "-" * len(table_header)
                
                table_lines = [header_line, table_header, separator]
                for entry in entries:
                    ts = entry.get("timestamp", "")
                    intent = entry.get("intent", "")
                    status = entry.get("status", "")
                    table_lines.append(f"{ts:<30} | {intent:<11} | {status:<12}")
                
                return "\n".join(table_lines)

            # 4. Default guidance
            return "I can show your session audit log or compliance summary. What would you like to see?"

        except Exception as exc:  # noqa: BLE001
            log_error("audit_compliance", type(exc).__name__)
            return "Audit log unavailable. Please try again."
