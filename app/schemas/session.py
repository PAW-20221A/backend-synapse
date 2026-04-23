from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class StartSessionRequest(BaseModel):
    quiz_id: UUID


class AnswerRequest(BaseModel):
    flashcard_id: UUID
    answer_given: int


class AnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: int
    selected_explanation: str
    correct_explanation: str


class SessionResponse(BaseModel):
    id: UUID
    quiz_id: UUID
    score: int | None
    total: int | None
    started_at: datetime
    finished_at: datetime | None

    model_config = {"from_attributes": True}
