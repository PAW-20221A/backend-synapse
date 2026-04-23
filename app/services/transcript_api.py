import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.video import Video

YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
    "youtube-nocookie.com",
    "www.youtube-nocookie.com",
}
YOUTUBE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")
WHITESPACE_PATTERN = re.compile(r"\s+")


class TranscriptServiceError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


@dataclass
class TranscriptResult:
    youtube_id: str
    youtube_url: str
    title: str | None
    language: str
    transcript: str
    video: Video


def normalize_transcript_text(raw_transcript: str | list[dict] | None) -> str:
    if isinstance(raw_transcript, list):
        chunks = [segment.get("text", "") for segment in raw_transcript]
        raw_transcript = " ".join(chunk for chunk in chunks if chunk)

    if not raw_transcript:
        return ""

    return WHITESPACE_PATTERN.sub(" ", raw_transcript).strip()


def extract_youtube_id(youtube_input: str) -> str:
    candidate = youtube_input.strip()
    if YOUTUBE_ID_PATTERN.fullmatch(candidate):
        return candidate

    if not candidate:
        raise TranscriptServiceError(422, "Invalid YouTube URL or video ID.")

    parsed = urlparse(candidate if "://" in candidate else f"https://{candidate}")
    host = parsed.netloc.lower()
    if host not in YOUTUBE_HOSTS:
        raise TranscriptServiceError(422, "Invalid YouTube URL or video ID.")

    path_parts = [part for part in parsed.path.split("/") if part]
    video_id = None

    if host.endswith("youtu.be"):
        video_id = path_parts[0] if path_parts else None
    elif parsed.path == "/watch":
        video_id = parse_qs(parsed.query).get("v", [None])[0]
    elif path_parts and path_parts[0] in {"shorts", "embed", "v", "live"}:
        video_id = path_parts[1] if len(path_parts) > 1 else None

    if not video_id or not YOUTUBE_ID_PATTERN.fullmatch(video_id):
        raise TranscriptServiceError(422, "Invalid YouTube URL or video ID.")

    return video_id


def canonical_youtube_url(youtube_id: str) -> str:
    return f"https://www.youtube.com/watch?v={youtube_id}"


class TranscriptAPIService:
    def __init__(self):
        self.base_url = settings.transcript_api_base_url.rstrip("/")
        self.api_key = settings.transcript_api_key

    def _build_result(self, video: Video) -> TranscriptResult:
        return TranscriptResult(
            youtube_id=video.youtube_id,
            youtube_url=video.youtube_url,
            title=video.title,
            language=video.language,
            transcript=video.transcript or "",
            video=video,
        )

    def _extract_error_message(self, response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return response.text or "Transcript provider request failed."

        detail = payload.get("detail")
        if isinstance(detail, dict):
            return detail.get("message") or "Transcript provider request failed."
        if isinstance(detail, str):
            return detail
        return payload.get("message") or "Transcript provider request failed."

    def _raise_for_response(self, response: httpx.Response) -> None:
        status_code = response.status_code
        if status_code == 404:
            raise TranscriptServiceError(404, "Transcript unavailable for this video.")
        if status_code in {400, 422}:
            raise TranscriptServiceError(422, "Invalid YouTube URL or video ID.")
        if status_code in {408, 429, 503}:
            raise TranscriptServiceError(
                503,
                "Transcript provider temporarily unavailable. Please try again.",
            )
        if status_code in {401, 402}:
            raise TranscriptServiceError(
                503,
                "Transcript provider is unavailable due to configuration or billing.",
            )

        detail = self._extract_error_message(response)
        raise TranscriptServiceError(502, f"Transcript provider error: {detail}")

    async def _fetch_remote_payload(self, youtube_url: str) -> dict:
        if not self.api_key:
            raise TranscriptServiceError(
                503,
                "Transcript provider is unavailable due to configuration or billing.",
            )

        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {
            "video_url": youtube_url,
            "format": "text",
            "include_timestamp": "false",
            "send_metadata": "true",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    f"{self.base_url}/youtube/transcript",
                    headers=headers,
                    params=params,
                )
        except httpx.RequestError as exc:
            raise TranscriptServiceError(
                503,
                "Transcript provider temporarily unavailable. Please try again.",
            ) from exc

        if response.status_code != 200:
            self._raise_for_response(response)

        try:
            return response.json()
        except ValueError as exc:
            raise TranscriptServiceError(502, "Transcript provider returned invalid JSON.") from exc

    async def get_transcript(self, db: Session, youtube_input: str) -> TranscriptResult:
        youtube_id = extract_youtube_id(youtube_input)
        youtube_url = canonical_youtube_url(youtube_id)

        video = db.query(Video).filter(Video.youtube_id == youtube_id).first()
        if video and video.transcript:
            return self._build_result(video)

        payload = await self._fetch_remote_payload(youtube_url)
        transcript = normalize_transcript_text(payload.get("transcript"))
        if not transcript:
            raise TranscriptServiceError(404, "Transcript unavailable for this video.")

        metadata = payload.get("metadata") or {}
        title = metadata.get("title") if isinstance(metadata, dict) else None
        language = payload.get("language") or (video.language if video else None) or "unknown"

        if video:
            video.youtube_url = youtube_url
            video.title = title
            video.language = language
            video.transcript = transcript
        else:
            video = Video(
                youtube_url=youtube_url,
                youtube_id=youtube_id,
                title=title,
                language=language,
                transcript=transcript,
            )
            db.add(video)

        db.commit()
        db.refresh(video)
        return self._build_result(video)


transcript_service = TranscriptAPIService()
