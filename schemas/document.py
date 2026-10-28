from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict


class DocumentListItem(BaseModel):
    id: int
    title: str
    source_type: Literal["upload", "url"]
    source_url: str | None
    file_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(DocumentListItem):
    extracted_text: str
