from pydantic import BaseModel, Field


class TranscriptRequest(BaseModel):
    url: str = Field(min_length=1)


class TranscriptResponse(BaseModel):
    youtube_id: str
    youtube_url: str
    title: str | None
    language: str
    transcript: str
