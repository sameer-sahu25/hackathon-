from pydantic import BaseModel
from typing import List


class DocumentChecklistItem(BaseModel):
    document: str
    why_needed: str
    where_to_get: str
    is_critical: bool


class ChecklistResponse(BaseModel):
    documents: List[DocumentChecklistItem]
    disclaimer: str
