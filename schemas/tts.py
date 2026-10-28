from pydantic import BaseModel, Field
from typing import Literal

language = Literal["twi", "ga", "ewe", "fante", "dagaare"]

class TTSRequest(BaseModel):
    document_id: int | None = Field(default=None, gt=0)
    text: str
    language: language
    voice: str


class TTSResponse(BaseModel):
    document_id: int | None = None
    audio_url: str
    duration_seconds: float
    language: language
    voice: str
