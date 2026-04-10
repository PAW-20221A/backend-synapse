from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.session import (
    AnswerRequest,
    AnswerResponse,
    SessionResponse,
    StartSessionRequest,
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("/", response_model=SessionResponse, status_code=201)
def start_session(
    body: StartSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # TODO: create study session
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/{session_id}/answer", response_model=AnswerResponse)
def submit_answer(
    session_id: UUID,
    body: AnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # TODO: process answer via tutor agent
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # TODO: fetch session state
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/{session_id}/finish", response_model=SessionResponse)
def finish_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # TODO: close session and persist score
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/", response_model=list[SessionResponse])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # TODO: list sessions for current user
    raise HTTPException(status_code=501, detail="Not implemented")
