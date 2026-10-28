from pydantic import BaseModel, ConfigDict,Field
from datetime import datetime



class ConversionHistoryResponse(BaseModel):
    document_id: int | None = None
    id: int
    title: str
    text: str
    voice:str
    language:str
    source_type: str
    audio_url: str | None
    created_at: datetime
    bookmarked : bool

    model_config = ConfigDict(from_attributes=True)


class ConversionHistoryCreate(BaseModel):
    document_id: int | None = Field(default=None, gt=0)
    title: str
    text: str
    voice:str
    language:str
    source_type: str
    audio_url: str | None = None
