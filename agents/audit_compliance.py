# agents/audit_compliance.py
# Purpose: Logs operations and checks actions for compliance with auditing standards.

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_AUDIT_DIR = Path(__file__).parent.parent / "data" / "audit_logs"
_MAX_ENTRIES = 10


class AuditComplianceAgent:
    """Agent that performs compliance audits and records session logs for security and tracking."""

    def run(self, input: str) -> str:  # noqa: A002
        """Return the last 10 sanitised audit log entries (timestamp, intent, status only)."""
        try:
            audit_dir = Path(os.getenv("AUDIT_LOG_DIR", str(_DEFAULT_AUDIT_DIR)))

            if not audit_dir.exists():
                return "No audit records found for this session."

            # Find the latest .jsonl file
            jsonl_files = sorted(audit_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not jsonl_files:
                return "No audit records found for this session."

            latest_file = jsonl_files[0]
            entries: list[dict] = []

            try:
                with open(latest_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            except Exception as exc:  # noqa: BLE001
                logger.error("AuditComplianceAgent: error reading log file type=%s", type(exc).__name__)
                return "Audit log unavailable."

            if not entries:
                return "No audit records found for this session."

            # Take last _MAX_ENTRIES, most recent last → reverse to show newest first
            recent = entries[-_MAX_ENTRIES:][::-1]

            lines = [f"Audit log — last {len(recent)} entries (most recent first):\n"]
            for i, entry in enumerate(recent, start=1):
                # Show only: timestamp, intent, status — never original input or PII
                timestamp = entry.get("timestamp", "N/A")
                intent = entry.get("intent", "N/A")
                status = entry.get("status", "N/A")
                lines.append(f"  {i:>2}. {timestamp}  intent={intent}  status={status}")

            return "\n".join(lines)

        except Exception as exc:  # noqa: BLE001
            logger.error("AuditComplianceAgent: unexpected error type=%s", type(exc).__name__)
            return "Audit log unavailable."
