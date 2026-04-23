import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.flashcard import Flashcard
from app.models.quiz import Quiz
from app.models.user import User
from app.services.quiz_agent import generate_quiz_from_transcript
from app.services.transcript_api import TranscriptServiceError, transcript_service
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
async def generate_quiz(
    body: GenerateQuizRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        transcript_result = await transcript_service.get_transcript(db, body.url)
        quiz_payload = await generate_quiz_from_transcript(
            transcript_result.transcript,
            body.question_count,
        )
    except TranscriptServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Quiz agent returned an invalid payload.",
        ) from exc

    quiz = Quiz(
        video_id=transcript_result.video.id,
        user_id=current_user.id,
        summary=quiz_payload.get("summary"),
    )
    db.add(quiz)
    db.flush()

    flashcards = []
    for index, flashcard_payload in enumerate(quiz_payload["flashcards"], start=1):
        flashcard = Flashcard(
            quiz_id=quiz.id,
            question=flashcard_payload["question"],
            options=flashcard_payload["options"],
            correct_answer=flashcard_payload["correct_answer"],
            explanations=flashcard_payload["explanations"],
            position=index,
        )
        flashcards.append(flashcard)

    db.add_all(flashcards)
    db.commit()
    db.refresh(quiz)
    return _serialize_quiz(db, quiz)


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
