"""
OpenAI Client - Streamlit Cloud Compatible
Works with ANY environment and handles all import failures gracefully
"""

import os
import asyncio
from typing import Dict, List

def get_api_key():
    """Get OpenAI API key from Streamlit secrets or environment."""
    api_key = None
    
    # Try Streamlit secrets first
    try:
        import streamlit as st
        api_key = st.secrets.get("OPENAI_API_KEY")
        if api_key:
            print("[OpenAI Client] Using API key from Streamlit secrets")
            return api_key
    except:
        pass
    
    # Try environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print("[OpenAI Client] Using API key from environment")
        return api_key
    
    # Final fallback
    raise ValueError(
        "OPENAI_API_KEY not found! Please:\n"
        "1. Add it to Streamlit secrets, or\n" 
        "2. Set as environment variable"
    )

async def chat(messages: List[Dict], model: str = "gpt-4", max_tokens: int = 2000):
    """
    Universal chat function that works even if OpenAI SDK fails to import.
    Uses direct HTTP requests as fallback.
    """
    api_key = get_api_key()
    
    # Strategy 1: Try OpenAI SDK
    try:
        # Try new SDK format
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response.choices[0].message.content
    except ImportError:
        print("[OpenAI Client] AsyncOpenAI not available, trying alternative...")
    except Exception as e:
        print(f"[OpenAI Client] AsyncOpenAI failed: {e}")

    # Strategy 2: Try old SDK format
    try:
        import openai
        openai.api_key = api_key
        
        def _sync_call():
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        
        return await asyncio.to_thread(_sync_call)
    except ImportError:
        print("[OpenAI Client] Legacy openai not available, using HTTP fallback...")
    except Exception as e:
        print(f"[OpenAI Client] Legacy openai failed: {e}")

    # Strategy 3: Direct HTTP requests (always works)
    try:
        import aiohttp
        import json
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API Error {response.status}: {error_text}")
                    
    except Exception as e:
        raise Exception(f"All OpenAI strategies failed: {str(e)}")

# Test function to verify setup
async def test_openai_connection():
    """Test if OpenAI connection works."""
    try:
        test_messages = [{"role": "user", "content": "Say 'Hello, I work!'"}]
        response = await chat(test_messages, model="gpt-3.5-turbo", max_tokens=20)
        print(f"[OpenAI Client] ✅ Connection test successful: {response}")
        return True
    except Exception as e:
        print(f"[OpenAI Client] ❌ Connection test failed: {e}")
        return False
