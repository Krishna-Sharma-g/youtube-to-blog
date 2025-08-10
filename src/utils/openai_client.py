from openai import AsyncOpenAI
from config.settings import get_settings

settings = get_settings()

client = AsyncOpenAI(api_key=settings["openai_api_key"])

async def chat(messages, model=None, **kwargs):
    response = await client.chat.completions.create(
        model=model or settings["openai_model"],
        messages=messages,
        **kwargs
    )
    return response.choices[0].message.content.strip()
