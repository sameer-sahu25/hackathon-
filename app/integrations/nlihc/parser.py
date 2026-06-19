import csv
from typing import List, Dict
from pydantic import BaseModel


class StateLawRecord(BaseModel):
    state: str
    notice_period_days: int
    just_cause_required: bool
    rent_control_status: str
    source_url: str
    last_updated: str


def parse_nlihc_csv(filepath: str) -> List[StateLawRecord]:
    records = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    record = StateLawRecord(
                        state=row.get("state", ""),
                        notice_period_days=int(row.get("notice_period_days", 30)),
                        just_cause_required=row.get("just_cause_required", "").lower() in ["true", "yes", "1"],
                        rent_control_status=row.get("rent_control_status", "none"),
                        source_url=row.get("source_url", ""),
                        last_updated=row.get("last_updated", "")
                    )
                    records.append(record)
                except Exception as e:
                    print(f"Skipping invalid row: {e}")
                    continue
    except Exception as e:
        print(f"Failed to parse CSV: {e}")
    return records
