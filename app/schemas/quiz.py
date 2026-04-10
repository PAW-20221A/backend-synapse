from uuid import UUID

from pydantic import BaseModel


class GenerateQuizRequest(BaseModel):
    url: str
    question_count: int = 5


class FlashcardResponse(BaseModel):
    id: UUID
    question: str
    options: list[str]
    correct_answer: int
    explanation: str
    position: int | None

    model_config = {"from_attributes": True}


class QuizResponse(BaseModel):
    id: UUID
    video_id: UUID
    user_id: UUID
    summary: str | None
    flashcards: list[FlashcardResponse]

    model_config = {"from_attributes": True}
