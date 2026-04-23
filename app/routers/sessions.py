from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.flashcard import Flashcard
from app.models.quiz import Quiz
from app.models.session import SessionAnswer, StudySession
from app.models.user import User
from app.schemas.session import (
    AnswerRequest,
    AnswerResponse,
    SessionResponse,
    StartSessionRequest,
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _serialize_session(session: StudySession) -> SessionResponse:
    return SessionResponse.model_validate(session)


def _get_owned_session(
    db: Session,
    session_id: UUID,
    user_id: UUID,
) -> StudySession:
    session = db.get(StudySession, session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )
    return session


def _count_quiz_flashcards(db: Session, quiz_id: UUID) -> int:
    return db.query(Flashcard).filter(Flashcard.quiz_id == quiz_id).count()


def _calculate_session_score(db: Session, session_id: UUID) -> int:
    return (
        db.query(SessionAnswer)
        .filter(
            SessionAnswer.session_id == session_id,
            SessionAnswer.is_correct.is_(True),
        )
        .count()
    )


@router.post("/", response_model=SessionResponse, status_code=201)
def start_session(
    body: StartSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quiz = db.get(Quiz, body.quiz_id)
    if not quiz or quiz.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found.",
        )

    session = StudySession(user_id=current_user.id, quiz_id=quiz.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return _serialize_session(session)


@router.post("/{session_id}/answer", response_model=AnswerResponse)
def submit_answer(
    session_id: UUID,
    body: AnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = _get_owned_session(db, session_id, current_user.id)
    if session.finished_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session has already been finished.",
        )

    flashcard = db.get(Flashcard, body.flashcard_id)
    if not flashcard or flashcard.quiz_id != session.quiz_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flashcard not found.",
        )

    if not 0 <= body.answer_given < len(flashcard.options):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected answer is out of range.",
        )

    existing_answer = (
        db.query(SessionAnswer)
        .filter(
            SessionAnswer.session_id == session.id,
            SessionAnswer.flashcard_id == flashcard.id,
        )
        .first()
    )
    if existing_answer:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This flashcard has already been answered in the session.",
        )

    is_correct = body.answer_given == flashcard.correct_answer
    answer = SessionAnswer(
        session_id=session.id,
        flashcard_id=flashcard.id,
        answer_given=body.answer_given,
        is_correct=is_correct,
    )
    db.add(answer)
    db.commit()

    return AnswerResponse(
        is_correct=is_correct,
        correct_answer=flashcard.correct_answer,
        selected_explanation=flashcard.explanations[body.answer_given],
        correct_explanation=flashcard.explanations[flashcard.correct_answer],
    )


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = _get_owned_session(db, session_id, current_user.id)
    return _serialize_session(session)


@router.post("/{session_id}/finish", response_model=SessionResponse)
def finish_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = _get_owned_session(db, session_id, current_user.id)

    session.score = _calculate_session_score(db, session.id)
    session.total = _count_quiz_flashcards(db, session.quiz_id)
    if session.finished_at is None:
        session.finished_at = datetime.now(timezone.utc)

    db.add(session)
    db.commit()
    db.refresh(session)
    return _serialize_session(session)


@router.get("/", response_model=list[SessionResponse])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sessions = (
        db.query(StudySession)
        .filter(StudySession.user_id == current_user.id)
        .order_by(StudySession.started_at.desc(), StudySession.id.desc())
        .all()
    )
    return [_serialize_session(session) for session in sessions]
