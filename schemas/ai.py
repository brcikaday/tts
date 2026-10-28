from pydantic import BaseModel,ConfigDict
from typing import Literal


language = Literal["twi", "ga", "ewe", "fante", "dagaare"]

class SummarizeRequest(BaseModel):
    text: str
    language: language

class SummarizeResponse(BaseModel):
    summary: str
    word_count: int

    model_config = ConfigDict(from_attributes=True)

class AskRequest(BaseModel):
    text: str
    question: str

class AskResponse(BaseModel):
    answer: str



class PodcastRequest(BaseModel):
    text: str
    language: str
    host_a_voice: str
    host_b_voice: str


class ScriptLine(BaseModel):
    host: str
    line: str

class PodcastResponse(BaseModel):
    script: list[ScriptLine]
    audio_url: str
    duration_seconds: float