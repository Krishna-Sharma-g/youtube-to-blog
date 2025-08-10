"""
OpenAI Client - Compatible with all OpenAI SDK versions
"""
import os
import asyncio
from typing import Dict, List

# Try new SDK first, fallback to old versions
try:
    from openai import AsyncOpenAI
    NEW_SDK = True
except ImportError:
    try:
        import openai
        NEW_SDK = False
    except ImportError:
        raise ImportError("OpenAI SDK not installed. Run: pip install openai>=1.3.0")

def get_openai_client():
    """Get OpenAI client with proper API key handling."""
    # Try environment variable first (for production)
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Fallback to Streamlit secrets (for local development)
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("OPENAI_API_KEY")
        except:
            pass
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found! Add it to Streamlit secrets or environment variables.")
    
    if NEW_SDK:
        return AsyncOpenAI(api_key=api_key)
    else:
        openai.api_key = api_key
        return openai

async def chat(messages: List[Dict], model: str = "gpt-4", max_tokens: int = 2000):
    """
    Universal chat function that works with any OpenAI SDK version.
    """
    client = get_openai_client()
    
    try:
        if NEW_SDK:
            # New SDK (v1.3.0+)
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        else:
            # Old SDK (fallback)
            def _sync_call():
                import openai
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                return response.choices[0].message.content
            
            # Run sync call in thread for async compatibility
            return await asyncio.to_thread(_sync_call)
            
    except Exception as e:
        print(f"OpenAI API Error: {str(e)}")
        raise e
