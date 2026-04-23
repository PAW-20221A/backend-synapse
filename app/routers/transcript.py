from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.transcript import TranscriptRequest, TranscriptResponse
from app.services.transcript_api import TranscriptServiceError, transcript_service

router = APIRouter(prefix="/api/transcript", tags=["transcript"])


@router.post("", response_model=TranscriptResponse)
async def get_transcript(
    body: TranscriptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user

    try:
        result = await transcript_service.get_transcript(db, body.url)
    except TranscriptServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return TranscriptResponse(
        youtube_id=result.youtube_id,
        youtube_url=result.youtube_url,
        title=result.title,
        language=result.language,
        transcript=result.transcript,
    )
