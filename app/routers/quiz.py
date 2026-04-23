from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.flashcard import Flashcard
from app.models.quiz import Quiz
from app.models.user import User
from app.schemas.quiz import FlashcardResponse, GenerateQuizRequest, QuizResponse

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


def _get_quiz_flashcards(db: Session, quiz_id: UUID) -> list[Flashcard]:
    return (
        db.query(Flashcard)
        .filter(Flashcard.quiz_id == quiz_id)
        .order_by(Flashcard.position.asc(), Flashcard.id.asc())
        .all()
    )


def _serialize_quiz(db: Session, quiz: Quiz) -> QuizResponse:
    flashcards = [
        FlashcardResponse.model_validate(flashcard)
        for flashcard in _get_quiz_flashcards(db, quiz.id)
    ]
    return QuizResponse(
        id=quiz.id,
        video_id=quiz.video_id,
        user_id=quiz.user_id,
        summary=quiz.summary,
        flashcards=flashcards,
    )


@router.post("/generate", response_model=QuizResponse)
def generate_quiz(
    body: GenerateQuizRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # TODO: implement quiz generation flow
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(
    quiz_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quiz = db.get(Quiz, quiz_id)
    if not quiz or quiz.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found.",
        )

    return _serialize_quiz(db, quiz)


@router.get("/", response_model=list[QuizResponse])
def list_quizzes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quizzes = (
        db.query(Quiz)
        .filter(Quiz.user_id == current_user.id)
        .order_by(Quiz.created_at.desc(), Quiz.id.desc())
        .all()
    )
    return [_serialize_quiz(db, quiz) for quiz in quizzes]
