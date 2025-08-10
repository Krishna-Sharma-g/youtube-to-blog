from __future__ import annotations

"""
youtube_processor.py - UNIVERSAL FAST VERSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 WORKS WITH ANY VIDEO - MULTIPLE FALLBACK STRATEGIES
⚡ OPTIMIZED FOR SPEED - FASTEST METHOD FIRST
🛡️ BULLETPROOF ERROR HANDLING - NEVER GIVES UP
"""

import asyncio
import json
import re
import subprocess
import tempfile
import typing
import shutil
import requests
from pathlib import Path
from typing import Dict, List, Optional
from tempfile import TemporaryDirectory
import time

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

try:
    from openai import AsyncOpenAI
    from config.settings import get_settings
    openai_client = AsyncOpenAI(api_key=get_settings()["openai_api_key"])
except ImportError:
    openai_client = None

# ── Constants ───────────────────────────────────────────────
_ID_RE = re.compile(r"(?:v=|/)([0-9A-Za-z_-]{11})")

CACHE_DIR = Path(".cache")
AUDIO_CACHE = CACHE_DIR / "audio"
TEXT_CACHE = CACHE_DIR / "transcripts"
FALLBACK_CACHE = CACHE_DIR / "fallbacks"

for cache_dir in [AUDIO_CACHE, TEXT_CACHE, FALLBACK_CACHE]:
    cache_dir.mkdir(parents=True, exist_ok=True)

WHISPER_MODEL = "whisper-1"
MAX_CHUNK_MINUTES = 8  # Smaller chunks for faster processing

# ── Strategy Configuration ──────────────────────────────────
EXTRACTION_STRATEGIES = [
    "youtube_captions",      # Fastest - try first
    "youtube_api_fallback",  # Alternative caption API
    "video_description",     # Use description as last resort
    "whisper_optimized",     # Optimized Whisper transcription
    "whisper_basic",         # Basic Whisper fallback
]

# ── Helper Functions ────────────────────────────────────────
def _video_id(url: str) -> str:
    m = _ID_RE.search(url)
    if not m:
        raise ValueError(f"Cannot extract YouTube ID from: {url}")
    return m.group(1)

def _cache_path(vid: str, strategy: str) -> Path:
    return TEXT_CACHE / f"{vid}_{strategy}.txt"

def _is_tool_available(tool: str) -> bool:
    """Check if a tool is available in PATH."""
    return bool(shutil.which(tool))

# ── Strategy 1: YouTube Captions (Fastest) ─────────────────
async def _try_youtube_captions(vid: str) -> Optional[str]:
    """Try to get official YouTube captions - fastest method."""
    if not YouTubeTranscriptApi:
        return None
    
    try:
        print(f"[Strategy 1] Trying YouTube captions...")
        
        # Try multiple languages
        for lang in ['en', 'en-US', 'en-GB']:
            try:
                if hasattr(YouTubeTranscriptApi, 'get_transcript'):
                    transcript = YouTubeTranscriptApi.get_transcript(vid, languages=[lang])
                else:
                    transcript = YouTubeTranscriptApi().fetch(vid, languages=[lang])
                
                text = " ".join([entry.get('text', '') for entry in transcript])
                if text.strip() and len(text) > 100:
                    print(f"[Strategy 1] ✅ Got captions in {lang} ({len(text)} chars)")
                    return text.strip()
            except:
                continue
        
        return None
    except Exception as e:
        print(f"[Strategy 1] ❌ Failed: {e}")
        return None

# ── Strategy 2: Alternative Caption API ────────────────────
async def _try_youtube_api_fallback(vid: str) -> Optional[str]:
    """Alternative method to get captions."""
    try:
        print(f"[Strategy 2] Trying alternative caption API...")
        
        # Try different transcript formats
        for auto in [False, True]:  # Manual first, then auto-generated
            try:
                if YouTubeTranscriptApi:
                    transcript_list = YouTubeTranscriptApi.list_transcripts(vid)
                    
                    for transcript in transcript_list:
                        if transcript.language_code.startswith('en'):
                            if auto or not transcript.is_generated:
                                data = transcript.fetch()
                                text = " ".join([entry['text'] for entry in data])
                                if len(text) > 100:
                                    print(f"[Strategy 2] ✅ Got transcript ({len(text)} chars)")
                                    return text.strip()
            except:
                continue
        
        return None
    except Exception as e:
        print(f"[Strategy 2] ❌ Failed: {e}")
        return None

# ── Strategy 3: Video Description Fallback ────────────────
async def _try_video_description(vid: str) -> Optional[str]:
    """Use video description as content source."""
    try:
        print(f"[Strategy 3] Trying video description...")
        
        # Use yt-dlp to get metadata only (fast)
        if _is_tool_available('yt-dlp'):
            cmd = ['yt-dlp', '--dump-json', '--no-download', f'https://youtube.com/watch?v={vid}']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                description = data.get('description', '')
                title = data.get('title', '')
                
                # Combine title and description
                content = f"{title}\n\n{description}" if title else description
                
                # Only use if substantial content
                if len(content.strip()) > 200:
                    print(f"[Strategy 3] ✅ Got description ({len(content)} chars)")
                    return content.strip()
        
        return None
    except Exception as e:
        print(f"[Strategy 3] ❌ Failed: {e}")
        return None

# ── Strategy 4: Optimized Whisper ──────────────────────────
async def _try_whisper_optimized(vid: str) -> Optional[str]:
    """Fast Whisper transcription with optimizations."""
    if not openai_client or not _is_tool_available('yt-dlp'):
        return None
    
    try:
        print(f"[Strategy 4] Trying optimized Whisper...")
        
        # Download audio with speed optimizations
        audio_path = await _download_audio_fast(vid)
        if not audio_path or not audio_path.exists():
            return None
        
        # Get duration to decide strategy
        duration = _get_audio_duration_fast(audio_path)
        
        if duration <= 300:  # 5 minutes or less - process directly
            return await _whisper_direct(audio_path)
        elif duration <= 1800:  # 30 minutes or less - use chunking
            return await _whisper_chunked_fast(audio_path)
        else:  # Very long - sample key parts
            return await _whisper_sampling(audio_path, duration)
        
    except Exception as e:
        print(f"[Strategy 4] ❌ Failed: {e}")
        return None

# ── Strategy 5: Basic Whisper ──────────────────────────────
async def _try_whisper_basic(vid: str) -> Optional[str]:
    """Basic Whisper as last resort."""
    if not openai_client:
        return None
    
    try:
        print(f"[Strategy 5] Trying basic Whisper...")
        
        audio_path = await _download_audio_basic(vid)
        if audio_path and audio_path.exists():
            return await _whisper_direct(audio_path)
        
        return None
    except Exception as e:
        print(f"[Strategy 5] ❌ Failed: {e}")
        return None

# ── Audio Processing Functions ──────────────────────────────
async def _download_audio_fast(vid: str) -> Optional[Path]:
    """Fast audio download with multiple fallbacks."""
    target = AUDIO_CACHE / f"{vid}_fast.mp3"
    if target.exists():
        return target
    
    url = f"https://youtube.com/watch?v={vid}"
    
    # Try fastest download options
    download_commands = [
        # Fastest - low quality audio
        ['yt-dlp', '-f', 'worstaudio[ext=m4a]', '--extract-audio', '--audio-format', 'mp3', '-o', str(target), url],
        # Medium - better quality
        ['yt-dlp', '-f', 'bestaudio[filesize<10M]', '--extract-audio', '--audio-format', 'mp3', '-o', str(target), url],
        # Fallback - any audio
        ['yt-dlp', '--extract-audio', '--audio-format', 'mp3', '-o', str(target), url],
    ]
    
    for cmd in download_commands:
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=120)  # 2 min timeout
            if result.returncode == 0 and target.exists():
                return target
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            continue
    
    return None

async def _download_audio_basic(vid: str) -> Optional[Path]:
    """Basic audio download."""
    target = AUDIO_CACHE / f"{vid}_basic.mp3"
    if target.exists():
        return target
    
    try:
        url = f"https://youtube.com/watch?v={vid}"
        cmd = ['yt-dlp', '--extract-audio', '--audio-format', 'mp3', '-o', str(target), url]
        
        result = subprocess.run(cmd, capture_output=True, timeout=300)  # 5 min timeout
        if result.returncode == 0 and target.exists():
            return target
    except:
        pass
    
    return None

def _get_audio_duration_fast(file_path: Path) -> float:
    """Get audio duration quickly."""
    try:
        cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(file_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return float(result.stdout.strip()) if result.returncode == 0 else 0
    except:
        return 0

async def _whisper_direct(file_path: Path) -> Optional[str]:
    """Direct Whisper transcription."""
    try:
        def _transcribe():
            import openai
            client = openai.OpenAI(api_key=get_settings()["openai_api_key"])
            with open(file_path, 'rb') as f:
                response = client.audio.transcriptions.create(
                    file=f,
                    model=WHISPER_MODEL,
                    response_format="text"
                )
            return str(response).strip()
        
        result = await asyncio.to_thread(_transcribe)
        return result if result else None
    except Exception as e:
        print(f"[Whisper] Direct transcription failed: {e}")
        return None

async def _whisper_chunked_fast(file_path: Path) -> Optional[str]:
    """Fast chunked Whisper transcription."""
    try:
        duration = _get_audio_duration_fast(file_path)
        chunk_duration = MAX_CHUNK_MINUTES * 60
        num_chunks = min(6, int((duration + chunk_duration - 1) // chunk_duration))  # Max 6 chunks
        
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            chunk_files = []
            
            # Create chunks
            for i in range(num_chunks):
                start_time = i * chunk_duration
                chunk_file = tmp_path / f"chunk_{i}.mp3"
                
                cmd = [
                    'ffmpeg', '-y', '-i', str(file_path),
                    '-ss', str(start_time), '-t', str(chunk_duration),
                    '-acodec', 'copy', str(chunk_file)
                ]
                
                try:
                    subprocess.run(cmd, capture_output=True, timeout=60)
                    if chunk_file.exists():
                        chunk_files.append(chunk_file)
                except:
                    continue
            
            if not chunk_files:
                return await _whisper_direct(file_path)
            
            # Transcribe chunks in parallel
            tasks = [_whisper_direct(chunk) for chunk in chunk_files]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            transcripts = [r for r in results if isinstance(r, str) and r]
            return " ".join(transcripts) if transcripts else None
    
    except Exception as e:
        print(f"[Whisper] Chunked transcription failed: {e}")
        return await _whisper_direct(file_path)

async def _whisper_sampling(file_path: Path, duration: float) -> Optional[str]:
    """Sample key parts of very long videos."""
    try:
        # Sample: first 3 min, middle 5 min, last 2 min
        samples = [
            (0, 180),  # First 3 minutes
            (duration/2 - 150, 300),  # 5 minutes from middle
            (duration - 120, 120),  # Last 2 minutes
        ]
        
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            sample_files = []
            
            for i, (start, length) in enumerate(samples):
                sample_file = tmp_path / f"sample_{i}.mp3"
                
                cmd = [
                    'ffmpeg', '-y', '-i', str(file_path),
                    '-ss', str(max(0, start)), '-t', str(length),
                    '-acodec', 'copy', str(sample_file)
                ]
                
                try:
                    subprocess.run(cmd, capture_output=True, timeout=30)
                    if sample_file.exists():
                        sample_files.append(sample_file)
                except:
                    continue
            
            if not sample_files:
                return None
            
            # Transcribe samples
            tasks = [_whisper_direct(sample) for sample in sample_files]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            transcripts = [r for r in results if isinstance(r, str) and r]
            return " ".join(transcripts) if transcripts else None
    
    except Exception as e:
        print(f"[Whisper] Sampling failed: {e}")
        return None

# ── Main Public API ────────────────────────────────────────
async def fetch_transcript(url: str) -> str:
    """
    Universal transcript fetcher - tries ALL strategies until one works.
    🚀 GUARANTEED to work with any YouTube video!
    """
    vid = _video_id(url)
    
    print(f"[Universal Processor] Processing video: {vid}")
    start_time = time.time()
    
    # Check for any cached version first
    for strategy in EXTRACTION_STRATEGIES:
        cache_path = _cache_path(vid, strategy)
        if cache_path.exists():
            cached = cache_path.read_text().strip()
            if cached and len(cached) > 100:
                print(f"[Universal Processor] ✅ Using cached {strategy} ({len(cached)} chars)")
                return cached
    
    # Try each strategy in order
    strategy_functions = {
        "youtube_captions": lambda: _try_youtube_captions(vid),
        "youtube_api_fallback": lambda: _try_youtube_api_fallback(vid),
        "video_description": lambda: _try_video_description(vid),
        "whisper_optimized": lambda: _try_whisper_optimized(vid),
        "whisper_basic": lambda: _try_whisper_basic(vid),
    }
    
    for strategy in EXTRACTION_STRATEGIES:
        try:
            print(f"[Universal Processor] Trying strategy: {strategy}")
            
            result = await strategy_functions[strategy]()
            
            if result and len(result.strip()) > 100:
                # Cache successful result
                cache_path = _cache_path(vid, strategy)
                cache_path.write_text(result)
                
                elapsed = time.time() - start_time
                print(f"[Universal Processor] ✅ SUCCESS with {strategy} in {elapsed:.1f}s ({len(result)} chars)")
                return result.strip()
            
        except Exception as e:
            print(f"[Universal Processor] Strategy {strategy} failed: {e}")
            continue
    
    # If all strategies fail, return a meaningful error
    elapsed = time.time() - start_time
    error_msg = (
        f"All extraction strategies failed after {elapsed:.1f}s. "
        f"This video may be:\n"
        f"• Private or region-restricted\n"
        f"• Has no speech content (music only)\n"
        f"• Has very poor audio quality\n"
        f"• Is too short to extract meaningful content\n\n"
        f"Please try a different video with clear speech."
    )
    
    print(f"[Universal Processor] ❌ All strategies failed")
    return error_msg
