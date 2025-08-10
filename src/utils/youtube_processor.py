from __future__ import annotations

"""
youtube_processor.py - WORKING CLOUD VERSION
Actually extracts real video content, not generic placeholders
"""

import asyncio
import json
import re
import subprocess
import requests
import time
from pathlib import Path
from typing import Optional

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    HAS_TRANSCRIPT_API = True
except ImportError:
    YouTubeTranscriptApi = None
    HAS_TRANSCRIPT_API = False

# ── Constants ───────────────────────────────────────────────
_ID_RE = re.compile(r"(?:v=|/)([0-9A-Za-z_-]{11})")

CACHE_DIR = Path(".cache")
TEXT_CACHE = CACHE_DIR / "transcripts"
TEXT_CACHE.mkdir(parents=True, exist_ok=True)

def _video_id(url: str) -> str:
    m = _ID_RE.search(url)
    if not m:
        raise ValueError(f"Cannot extract YouTube ID from: {url}")
    return m.group(1)

def _cache_path(vid: str) -> Path:
    return TEXT_CACHE / f"{vid}.txt"

async def _get_youtube_captions_working(vid: str) -> Optional[str]:
    """Actually working caption extraction."""
    if not HAS_TRANSCRIPT_API:
        print("[Processor] youtube-transcript-api not available")
        return None
    
    try:
        print(f"[Processor] Extracting captions for {vid}...")
        
        # Try multiple approaches
        approaches = [
            # Approach 1: Direct transcript
            lambda: YouTubeTranscriptApi.get_transcript(vid, languages=['en']),
            lambda: YouTubeTranscriptApi.get_transcript(vid, languages=['en-US']),
            lambda: YouTubeTranscriptApi.get_transcript(vid, languages=['en-GB']),
            # Approach 2: Auto-generated
            lambda: YouTubeTranscriptApi.get_transcript(vid),
        ]
        
        for i, approach in enumerate(approaches, 1):
            try:
                print(f"[Processor] Trying approach {i}...")
                transcript_data = approach()
                
                if transcript_data:
                    # Combine all text entries
                    text = " ".join([entry.get('text', '') for entry in transcript_data])
                    text = text.strip()
                    
                    if len(text) > 200:  # Ensure substantial content
                        print(f"[Processor] ✅ SUCCESS: Got {len(text)} chars via approach {i}")
                        return text
                        
            except Exception as e:
                print(f"[Processor] Approach {i} failed: {type(e).__name__}")
                continue
        
        print("[Processor] All caption approaches failed")
        return None
        
    except Exception as e:
        print(f"[Processor] Caption extraction error: {e}")
        return None

async def _get_video_metadata_working(vid: str) -> Optional[str]:
    """Extract video metadata when captions fail."""
    try:
        print(f"[Processor] Trying metadata extraction for {vid}...")
        
        # Method 1: Web scraping (most reliable in cloud)
        url = f"https://www.youtube.com/watch?v={vid}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            html = response.text
            
            # Extract title with multiple patterns
            title = ""
            title_patterns = [
                r'<title>([^<]+)</title>',
                r'"title":"([^"]+)"',
                r'<meta property="og:title" content="([^"]*)"',
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, html)
                if match:
                    title = match.group(1).replace(' - YouTube', '').strip()
                    break
            
            # Extract description
            description = ""
            desc_patterns = [
                r'"shortDescription":"([^"]+)"',
                r'<meta name="description" content="([^"]*)"',
                r'"description":{"simpleText":"([^"]+)"',
            ]
            
            for pattern in desc_patterns:
                match = re.search(pattern, html)
                if match:
                    description = match.group(1).strip()
                    break
            
            # Combine title and description
            content_parts = []
            if title and len(title) > 10:
                content_parts.append(f"Title: {title}")
            if description and len(description) > 20:
                content_parts.append(f"Description: {description}")
            
            if content_parts:
                full_content = "\n\n".join(content_parts)
                print(f"[Processor] ✅ Got metadata: {len(full_content)} chars")
                return full_content
        
        print("[Processor] Metadata extraction failed")
        return None
        
    except Exception as e:
        print(f"[Processor] Metadata error: {e}")
        return None

async def fetch_transcript(url: str) -> str:
    """
    Fetch actual video transcript - not generic content.
    """
    vid = _video_id(url)
    cache_path = _cache_path(vid)
    
    print(f"[Processor] Processing video: {vid}")
    
    # Check cache
    if cache_path.exists():
        cached = cache_path.read_text().strip()
        if cached and len(cached) > 200:
            print(f"[Processor] Using cached content ({len(cached)} chars)")
            return cached
    
    # Try caption extraction
    transcript = await _get_youtube_captions_working(vid)
    
    if not transcript or len(transcript) < 100:
        print("[Processor] Captions failed, trying metadata...")
        transcript = await _get_video_metadata_working(vid)
    
    # Validate we got real content
    if transcript and len(transcript) > 100:
        # Check it's not generic content
        generic_indicators = [
            'this video', 'the video', 'video content', 'content analysis',
            'insights from', 'key takeaways', 'important concepts'
        ]
        
        transcript_lower = transcript.lower()
        generic_count = sum(1 for indicator in generic_indicators if indicator in transcript_lower)
        
        # If it has specific content (not just generic phrases)
        if generic_count < 3 and any(char.isdigit() or char in '.,!?;:' for char in transcript):
            cache_path.write_text(transcript)
            print(f"[Processor] ✅ SUCCESS: Real content extracted ({len(transcript)} chars)")
            return transcript
    
    # If we reach here, we failed to get real content
    error_msg = (
        f"Could not extract meaningful content from video {vid}. "
        f"This video may:\n"
        f"• Be private, age-restricted, or region-locked\n"
        f"• Have no speech content (music/instrumental only)\n"
        f"• Have disabled captions and unclear audio\n"
        f"• Be too short or have no substantial content\n\n"
        f"Please try a different video with:\n"
        f"• Clear speech and dialogue\n"
        f"• Educational or tutorial content\n"
        f"• Enabled captions/subtitles\n"
        f"• At least 5+ minutes of content"
    )
    
    print("[Processor] ❌ Failed to extract real content")
    return error_msg
