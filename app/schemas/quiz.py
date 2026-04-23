from uuid import UUID

from pydantic import BaseModel, Field


class GenerateQuizRequest(BaseModel):
    url: str = Field(min_length=1)
    question_count: int = Field(default=5, ge=1)


class FlashcardResponse(BaseModel):
    id: UUID
    question: str
    options: list[str]
    correct_answer: int
    explanations: list[str]
    position: int | None

    model_config = {"from_attributes": True}


class QuizResponse(BaseModel):
    id: UUID
    video_id: UUID
    user_id: UUID
    summary: str | None
    flashcards: list[FlashcardResponse]

    model_config = {"from_attributes": True}
