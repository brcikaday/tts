from pydantic import BaseModel, ConfigDict,HttpUrl


class ScrapeRequest(BaseModel):
    url: HttpUrl


class ScrapeResponse(BaseModel):
    document_id: int
    source_type: str
    extracted_text: str
    title: str
    text: str
    word_count: int
    source_url: HttpUrl

    model_config = ConfigDict(from_attributes=True)
