import httpx

from app.core.config import settings


class SubTublyService:
    def __init__(self):
        self.base_url = settings.subtubly_api_url
        self.api_key = settings.subtubly_api_key

    async def get_transcript(self, youtube_url: str) -> dict:
        """Fetches transcript for a YouTube video from the SubTubly API."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient() as client:
            response = client.post(
                f"{self.base_url}/transcribe",
                headers=headers,
                json={"url": youtube_url},
                timeout=60.0,
            )
            response.raise_for_status()
            return response.json()


subtubly_service = SubTublyService()
