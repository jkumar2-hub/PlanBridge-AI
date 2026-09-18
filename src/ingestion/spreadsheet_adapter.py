"""Spreadsheet Ingestion Adapter for multi-row discipline CSV/Excel logs."""
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd


class SpreadsheetAdapter:
    # Column mapping aliases
    DESC_COLS = ["activity_description", "description", "activity", "task", "work_description", "item_description"]
    DISC_COLS = ["discipline", "trade", "department", "dept"]
    DATE_COLS = ["report_date", "date", "event_date", "log_date", "timestamp"]
    ACTION_COLS = ["status", "action_type", "state", "progress_status"]
    LOC_COLS = ["location", "area", "unit", "zone"]

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Spreadsheet not found: {file_path}")

        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path, encoding="utf-8-sig")
        else:
            df = pd.read_excel(path)

        return self.parse_dataframe(df, filename=path.name)

    def parse_dataframe(self, df: pd.DataFrame, filename: Optional[str] = None) -> Dict[str, Any]:
        report_id = f"REP-XLS-{uuid.uuid4().hex[:8]}"

        # Normalize column names
        col_map = {}
        for col in df.columns:
            clean_col = str(col).strip().lower().replace(" ", "_").replace("-", "_")
            col_map[clean_col] = col

        def find_val(row: pd.Series, candidates: List[str]) -> Optional[str]:
            for c in candidates:
                if c in col_map:
                    val = row[col_map[c]]
                    if pd.notna(val) and str(val).strip():
                        return str(val).strip()
            return None

        rows_data = []
        for _, row in df.iterrows():
            desc = find_val(row, self.DESC_COLS)
            if not desc:
                continue
            disc = find_val(row, self.DISC_COLS)
            date_val = find_val(row, self.DATE_COLS)
            action = find_val(row, self.ACTION_COLS) or "in-progress"
            loc = find_val(row, self.LOC_COLS)

            rows_data.append({
                "description": desc,
                "discipline": disc,
                "date": date_val,
                "action": action,
                "location": loc,
                "raw_row": row.to_dict(),
            })

        return {
            "report_id": report_id,
            "source_format": "spreadsheet",
            "raw_text": f"Spreadsheet import: {filename or 'data_file'} ({len(rows_data)} rows)",
            "discipline_hint": rows_data[0]["discipline"] if rows_data else None,
            "reported_by": "Spreadsheet Importer",
            "timestamp_received": datetime.now().isoformat(),
            "filename": filename,
            "rows": rows_data,
        }
