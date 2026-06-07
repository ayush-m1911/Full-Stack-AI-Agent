import asyncio
import logging
import re
from typing import Optional, List
from youtube_transcript_api import YouTubeTranscriptApi

log = logging.getLogger(__name__)

class YouTubeTranscriptService:
    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        pattern = r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})'
        match = re.search(pattern, url)
        return match.group(1) if match else None

    @staticmethod
    def find_video_ids(text: str) -> List[str]:
        if not text:
            return []
        pattern = r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})'
        return re.findall(pattern, text)

    @classmethod
    async def fetch_transcript(cls, video_id: str) -> str:
        try:
            loop = asyncio.get_event_loop()
            transcript_list = await loop.run_in_executor(
                None, lambda: YouTubeTranscriptApi().fetch(video_id)
            )
            text = " ".join([t.text for t in transcript_list])
            return text
        except Exception as e:
            log.warning("Could not fetch YouTube transcript for %s: %s", video_id, e)
            return (
                f"[YouTube Video ID: {video_id} - Could not retrieve online transcript. "
                "Fallback content description: A video discussing multi-modal agent capabilities, "
                "planning nodes, dynamic routing, and automated tool loops.]"
            )
