from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.quiz import GenerateQuizRequest, QuizResponse

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


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
    # TODO: fetch quiz by ID
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/", response_model=list[QuizResponse])
def list_quizzes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # TODO: list quizzes for current user
    raise HTTPException(status_code=501, detail="Not implemented")
