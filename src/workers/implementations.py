from __future__ import annotations
import requests
import json
import os
import streamlit as st
from typing import List, Dict, Optional

# -----------------------
# Utilities
# -----------------------

def get_api_key() -> str:
    try:
        key = st.secrets["OPENAI_API_KEY"]
        if key and key.startswith("sk-"):
            return key
    except Exception:
        pass
    key = os.getenv("OPENAI_API_KEY")
    if key and key.startswith("sk-"):
        return key
    raise ValueError("OpenAI API key not found or invalid format")

def call_openai(messages: List[Dict], max_tokens: int = 1200, temperature: float = 0.8) -> str:
    api_key = get_api_key()
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "presence_penalty": 0.2,
        "frequency_penalty": 0.2
    }
    resp = requests.post("https://api.openai.com/v1/chat/completions",
                         headers=headers, json=payload, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(f"OpenAI API Error {resp.status_code}: {resp.text[:400]}")
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()

def persona_system_message() -> Dict:
    return {
        "role": "system",
        "content": (
            "You are a machine learning researcher and educator. "
            "Your audience is ML enthusiasts of all ages. "
            "Write like you’re talking to a smart friend: conversational, direct, and occasionally witty. "
            "Vary sentence length. Use transitions like “Here’s the thing,” “Let’s be honest,” “What I’ve found is…”. "
            "Avoid buzzwords and corporate talk. Never use words like “delve,” “leverage,” “robust,” "
            "“seamless,” “cutting-edge,” “game-changing,” “furthermore,” “navigate,” “elevate,” “comprehensive.” "
            "Keep everything concrete, readable, and useful."
        )
    }

def chunk_text(text: str, max_words: int = 800) -> List[str]:
    words = text.split()
    chunks = []
    cur = []
    count = 0
    for w in words:
        cur.append(w)
        count += 1
        if count >= max_words:
            chunks.append(" ".join(cur))
            cur = []
            count = 0
    if cur:
        chunks.append(" ".join(cur))
    return chunks

# -----------------------
# Base Worker
# -----------------------

class BaseWorker:
    def __init__(self, name: str):
        self.name = name  # expected names: 'title', 'intro', etc.

    async def generate(self, transcript: str) -> str:
        # Call synchronous generation in a thread to keep async compatibility
        import asyncio
        return await asyncio.to_thread(self._generate_sync, transcript)

    def _generate_sync(self, transcript: str) -> str:
        # To be implemented by subclasses
        raise NotImplementedError

    # Helper to build messages with persona
    def _messages(self, task_instructions: str, user_payload: str) -> List[Dict]:
        return [
            persona_system_message(),
            {"role": "system", "content": task_instructions},
            {"role": "user", "content": user_payload}
        ]

# -----------------------
# Title Worker
# -----------------------

class TitleWorker(BaseWorker):
    def __init__(self):
        super().__init__("title")

    def _generate_sync(self, transcript: str) -> str:
        chunks = chunk_text(transcript, 400)
        first = chunks[0] if chunks else transcript[:1200]
        task = (
            "Write a single H1 blog title (prefix with #). 8–14 words, human and specific to this video. "
            "Avoid generic phrases like “Insights and Analysis” or “Deep Dive”."
        )
        messages = self._messages(task, f"Transcript excerpt:\n\n{first}\n\nNow write the title.")
        out = call_openai(messages, max_tokens=80, temperature=0.7)
        if not out.startswith("#"):
            out = "# " + out
        return out

# -----------------------
# Intro (Lede) Worker
# -----------------------

class IntroWorker(BaseWorker):
    def __init__(self):
        super().__init__("intro")

    def _generate_sync(self, transcript: str) -> str:
        chunks = chunk_text(transcript, 600)
        first = chunks if chunks else transcript[:1500]
        task = (
            "Write a 150–250-word lede that hooks with a relatable line, frames what the video is about, "
            "and promises 2–3 concrete things the reader will learn. Use first or second person. "
            "No corporate phrasing."
        )
        messages = self._messages(task, f"Use this content to ground your lede:\n\n{first}")
        return call_openai(messages, max_tokens=280)

# -----------------------
# Context Worker (NEW)
# -----------------------

class ContextWorker(BaseWorker):
    def __init__(self):
        super().__init__("context")

    def _generate_sync(self, transcript: str) -> str:
        chunks = chunk_text(transcript, 600)
        anchor = chunks if chunks else transcript[:1500]
        task = (
            "Write 120–200 words of context: who’s speaking (use any channel/title cues if present), "
            "why this topic matters now, and what assumptions the viewer might bring. "
            "If metadata is limited, say “from the video’s flow, it’s likely…” instead of making hard claims."
        )
        messages = self._messages(task, f"Ground this context in the following:\n\n{anchor}")
        return call_openai(messages, max_tokens=240)

# -----------------------
# Key Points / Body Sections Worker
# -----------------------

class KeyPointsWorker(BaseWorker):
    def __init__(self):
        super().__init__("key_points")

    def _generate_sync(self, transcript: str) -> str:
        # Use middle chunk to avoid repeating intro
        chunks = chunk_text(transcript, 800)
        mid = chunks[len(chunks)//2] if chunks else transcript[:1800]
        task = (
            "Write a 220–350-word body section with a subheading (## ...). "
            "Explain one concrete idea grounded in the transcript. Add your take: when it works, where it fails, "
            "and one practical step to try this week. Human, not academic."
        )
        messages = self._messages(task, f"Use this section to ground your writing:\n\n{mid}")
        return call_openai(messages, max_tokens=420)

# -----------------------
# Quotes Worker
# -----------------------

class QuotesWorker(BaseWorker):
    def __init__(self):
        super().__init__("quotes")

    def _generate_sync(self, transcript: str) -> str:
        # Use most-content chunk (rough heuristic: the longest chunk)
        chunks = chunk_text(transcript, 800)
        ref = max(chunks, key=len) if chunks else transcript[:2000]
        task = (
            "Pull 2–3 meaningful lines (quote or clearly marked paraphrase) from the content. "
            "For each, add 2–3 sentences of commentary: why it matters, when it breaks, how to apply. "
            "Avoid generic statements."
        )
        messages = self._messages(task, f"Ground in this content:\n\n{ref}")
        return call_openai(messages, max_tokens=500)

# -----------------------
# Summary Worker
# -----------------------

class SummaryWorker(BaseWorker):
    def __init__(self):
        super().__init__("summary")

    def _generate_sync(self, transcript: str) -> str:
        base = transcript[-1800:] if len(transcript) > 2000 else transcript
        task = (
            "Write a 150–220-word synthesis that connects themes. No bullet re-lists. "
            "Make one or two thoughtful connections a practitioner would care about."
        )
        messages = self._messages(task, f"Base your synthesis on:\n\n{base}")
        out = call_openai(messages, max_tokens=280)
        if not out.startswith("##"):
            out = "## The Big Picture\n\n" + out
        return out

# -----------------------
# What This Means Worker (NEW)
# -----------------------

class WhatThisMeansWorker(BaseWorker):
    def __init__(self):
        super().__init__("what_this_means_for_you")

    def _generate_sync(self, transcript: str) -> str:
        tail = transcript[-1500:] if len(transcript) > 1500 else transcript
        task = (
            "Write 150–250 words titled 'What this means for you'. "
            "Translate 2–3 ideas into actions or checks: what to start, stop, or continue. Make it concrete."
        )
        messages = self._messages(task, f"Base this on:\n\n{tail}")
        out = call_openai(messages, max_tokens=260)
        if not out.lower().startswith("## what this means"):
            out = "## What this means for you\n\n" + out
        return out

# -----------------------
# Conclusion Worker
# -----------------------

class ConclusionWorker(BaseWorker):
    def __init__(self):
        super().__init__("conclusion")

    def _generate_sync(self, transcript: str) -> str:
        tail = transcript[-1200:] if len(transcript) > 1400 else transcript
        task = (
            "Write 120–200 words that land one memorable takeaway, acknowledge a trade-off, "
            "and end with a small CTA (e.g., try X this week). No clichés."
        )
        messages = self._messages(task, f"Use this ending context:\n\n{tail}")
        out = call_openai(messages, max_tokens=220)
        if not out.startswith("##"):
            out = "## Wrapping up\n\n" + out
        return out

# -----------------------
# SEO Worker
# -----------------------

class SEOWorker(BaseWorker):
    def __init__(self):
        super().__init__("seo")

    def _generate_sync(self, transcript: str) -> str:
        task = (
            "Create SEO metadata for ML readers. "
            "Meta description <=160 characters, human-sounding. "
            "Keywords: 6–10 realistic phrases ML folks actually search. "
            "Format:\nMETA_DESCRIPTION: \"...\"\nKEYWORDS: \"k1, k2, ...\""
        )
        messages = self._messages(task, f"Use this for context:\n\n{transcript[:1200]}")
        return call_openai(messages, max_tokens=160, temperature=0.6)

# -----------------------
# Tags Worker
# -----------------------

class TagsWorker(BaseWorker):
    def __init__(self):
        super().__init__("tags")

    def _generate_sync(self, transcript: str) -> str:
        task = (
            "Generate 8–12 ML-relevant hashtags that people actually search. "
            "Mix popular and specific ones. Format: 'Tags: #tag1 #tag2 ...'"
        )
        messages = self._messages(task, f"Topic context:\n\n{transcript[:1000]}")
        out = call_openai(messages, max_tokens=80, temperature=0.6)
        if not out.lower().startswith("tags:"):
            out = "Tags: " + out
        return out
