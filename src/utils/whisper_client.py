import os, aiofiles
from pathlib import Path
from tempfile import NamedTemporaryFile
from openai import AsyncOpenAI
from config.settings import get_settings

settings = get_settings()
client    = AsyncOpenAI(api_key=settings["openai_api_key"])

WHISPER_MODEL = "whisper-1"          # change if you use a fine-tune

async def transcribe_audio(file_path: Path) -> str:
    """
    Send a local audio file to Whisper and return the plain-text transcript.
    """
    async with aiofiles.open(file_path, "rb") as af:
        response = await client.audio.transcriptions.create(
            file=af,
            model=WHISPER_MODEL,
            response_format="text",
            language="en"        # leave blank for auto-detect
        )
    return response.strip()
