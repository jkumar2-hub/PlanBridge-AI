"""Text Ingestion Adapter for free-text daily reports and supervisor diaries."""
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class TextAdapter:
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Report file not found: {file_path}")

        raw_text = path.read_text(encoding="utf-8-sig")
        return self.parse_text(raw_text, filename=path.name)

    def parse_text(self, raw_text: str, filename: Optional[str] = None) -> Dict[str, Any]:
        report_id = f"REP-{uuid.uuid4().hex[:8]}"

        discipline_hint = None
        for disc in ["Civil", "Piping", "Electrical", "Instrumentation", "HSE"]:
            if re.search(rf"\b{disc}\b", raw_text, re.IGNORECASE):
                discipline_hint = disc
                break

        reported_by = None
        m_reporter = re.search(r"(?:Supervisor|Reporter|Site Eng|Inspector|Reported by|Logged by):\s*([^\r\n]+)", raw_text, re.IGNORECASE)
        if m_reporter:
            reported_by = m_reporter.group(1).strip()

        return {
            "report_id": report_id,
            "source_format": "free_text",
            "raw_text": raw_text.strip(),
            "discipline_hint": discipline_hint,
            "reported_by": reported_by or "Site Field Staff",
            "timestamp_received": datetime.now().isoformat(),
            "filename": filename,
        }
