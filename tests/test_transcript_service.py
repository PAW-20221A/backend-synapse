import unittest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.models.video import Video
from app.services.transcript_api import (
    TranscriptAPIService,
    TranscriptServiceError,
    extract_youtube_id,
    normalize_transcript_text,
)


class TranscriptHelpersTests(unittest.TestCase):
    def test_extract_youtube_id_supports_supported_formats(self):
        expected_id = "dQw4w9WgXcQ"
        cases = [
            expected_id,
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/shorts/dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
        ]

        for value in cases:
            with self.subTest(value=value):
                self.assertEqual(extract_youtube_id(value), expected_id)

    def test_normalize_transcript_text_collapses_whitespace(self):
        raw_transcript = "Primeira linha\n\nSegunda\tlinha   com   espacos"

        normalized = normalize_transcript_text(raw_transcript)

        self.assertEqual(normalized, "Primeira linha Segunda linha com espacos")


class TranscriptAPIServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.service = TranscriptAPIService()
        self.service.api_key = "test-key"
        self.video = Video(
            id=uuid.uuid4(),
            youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            youtube_id="dQw4w9WgXcQ",
            title="Saved Title",
            transcript="Texto salvo em cache",
            language="en",
        )

    async def test_get_transcript_uses_cached_video_without_remote_call(self):
        db = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.first.return_value = self.video
        db.query.return_value = query

        with patch.object(
            self.service,
            "_fetch_remote_payload",
            new=AsyncMock(),
        ) as mocked_fetch:
            result = await self.service.get_transcript(db, self.video.youtube_id)

        self.assertEqual(result.transcript, self.video.transcript)
        self.assertEqual(result.title, self.video.title)
        mocked_fetch.assert_not_awaited()
        db.commit.assert_not_called()

    async def test_get_transcript_persists_remote_response_with_metadata(self):
        db = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.first.return_value = None
        db.query.return_value = query

        payload = {
            "video_id": self.video.youtube_id,
            "language": "pt",
            "transcript": "Linha 1\nLinha 2",
            "metadata": {"title": "Novo titulo"},
        }

        with patch.object(
            self.service,
            "_fetch_remote_payload",
            new=AsyncMock(return_value=payload),
        ):
            result = await self.service.get_transcript(db, self.video.youtube_url)

        persisted_video = db.add.call_args.args[0]
        self.assertEqual(persisted_video.youtube_id, self.video.youtube_id)
        self.assertEqual(persisted_video.youtube_url, self.video.youtube_url)
        self.assertEqual(persisted_video.title, "Novo titulo")
        self.assertEqual(persisted_video.language, "pt")
        self.assertEqual(persisted_video.transcript, "Linha 1 Linha 2")
        self.assertEqual(result.transcript, "Linha 1 Linha 2")
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    def test_raise_for_response_maps_expected_statuses(self):
        cases = [
            (404, {"detail": "not found"}, 404, "Transcript unavailable"),
            (408, {"detail": "timeout"}, 503, "temporarily unavailable"),
            (429, {"detail": "limited"}, 503, "temporarily unavailable"),
            (503, {"detail": "down"}, 503, "temporarily unavailable"),
            (401, {"detail": "bad auth"}, 503, "configuration or billing"),
            (
                402,
                {"detail": {"message": "no credits"}},
                503,
                "configuration or billing",
            ),
        ]

        for status_code, payload, expected_status, expected_message in cases:
            with self.subTest(status_code=status_code):
                response = httpx.Response(
                    status_code=status_code,
                    json=payload,
                    request=httpx.Request("GET", "https://transcriptapi.com/api/v2/youtube/transcript"),
                )

                with self.assertRaises(TranscriptServiceError) as ctx:
                    self.service._raise_for_response(response)

                self.assertEqual(ctx.exception.status_code, expected_status)
                self.assertIn(expected_message, ctx.exception.detail)
