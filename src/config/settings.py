from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).resolve().parents[1] / '.env')

@lru_cache
def get_settings():
    return {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "openai_model":  os.getenv("OPENAI_MODEL", "gpt-5-mini"),
    }
