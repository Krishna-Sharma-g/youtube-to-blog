from __future__ import annotations
import asyncio
from typing import Dict, List
import re
import time
import traceback

from workers.implementations import (
    TitleWorker, IntroWorker, ContextWorker, KeyPointsWorker,
    QuotesWorker, SummaryWorker, WhatThisMeansWorker, ConclusionWorker,
    SEOWorker, TagsWorker, chunk_text
)
from utils.youtube_processor import fetch_transcript

BANNED_PHRASES = [
    "this video provides valuable insights",
    "this content covers important topics",
    "in today’s fast-paced world",
    "let me break down",
    "insights and analysis",
    "deep dive",
]

def is_low_quality(text: str, min_words: int) -> bool:
    if not text or len(text.strip()) == 0:
        return True
    words = len(text.strip().split())
    if words < min_words:
        return True
    lower = text.lower()
    if any(p in lower for p in BANNED_PHRASES):
        return True
    return False

def corrective_instruction(original_task: str, min_words: int) -> str:
    return (
        original_task
        + f"\n\nThe previous attempt was too generic/short. Expand to at least {min_words} words. "
          "Use 1 concrete example and 1 practical suggestion. Avoid filler phrases and banned buzzwords."
    )

class BlogOrchestrator:
    """
    Human-quality blog orchestrator with routing, retries, and quality gates.
    Accepts all videos and enhances thin transcripts.
    """

    def __init__(self):
        self.workers = {
            "title": TitleWorker(),
            "intro": IntroWorker(),
            "context": ContextWorker(),
            "key_points_1": KeyPointsWorker(),
            "key_points_2": KeyPointsWorker(),
            "quotes": QuotesWorker(),
            "summary": SummaryWorker(),
            "what_this_means_for_you": WhatThisMeansWorker(),
            "conclusion": ConclusionWorker(),
            "seo": SEOWorker(),
            "tags": TagsWorker(),
        }

    def _enhance_if_thin(self, transcript: str, youtube_url: str) -> str:
        if not transcript or len(transcript.strip()) < 200:
            video_id = "unknown"
            if "v=" in youtube_url:
                video_id = youtube_url.split("v=")[-1].split("&")[0]
            enhanced = (
                f"Video ID: {video_id}\n"
                "This video includes visual and audio content likely aimed at educating, informing, or inspiring its audience. "
                "While full transcript detail may be limited, we can still extract themes, practical ideas, and meaningful takeaways. "
                "Use the following description as a minimal basis and expand with careful, honest commentary."
            )
            return (transcript or "") + "\n\n" + enhanced
        return transcript

    async def _run_with_retry(self, worker, transcript: str, min_words: int, task_hint: str = "") -> str:
        """
        Runs a worker once; if low quality, attempts one corrective retry by appending
        corrective instruction to the system message via a hint string.
        """
        try:
            out = await worker.generate(transcript)
            if not is_low_quality(out, min_words):
                return out
            # Retry once with stronger instruction if worker supports indirect task usage
            # For our workers, we use the same internal prompt; we can nudge via transcript suffix
            # without modifying worker code.
            augmented_transcript = transcript + (
                "\n\n[Writer Note] The previous draft was too generic. "
                "Make it concrete, use one example, and add one practical suggestion. "
                "Avoid banned phrases."
            )
            out2 = await worker.generate(augmented_transcript)
            return out2
        except Exception as e:
            print(f"[Retry] Worker {worker.name} failed: {e}")
            return ""  # will be replaced by fallback in assembly

    def _transition(self, phrase: str) -> str:
        return f"\n\n_{phrase}_\n\n"

    def _assemble(self, sections: Dict[str, str]) -> str:
        parts = []

        title = sections.get("title", "").strip()
        if title:
            parts.append(title)

        intro = sections.get("intro", "").strip()
        if intro:
            parts.append(intro)

        context = sections.get("context", "").strip()
        if context:
            parts.append(context)

        kp1 = sections.get("key_points_1", "").strip()
        kp2 = sections.get("key_points_2", "").strip()
        if kp1:
            parts.append(self._transition("Here’s where it gets useful…"))
            parts.append(kp1)
        if kp2:
            parts.append(kp2)

        quotes = sections.get("quotes", "").strip()
        if quotes:
            parts.append(self._transition("Let’s pull a couple of lines that stuck with me…"))
            parts.append("## Lines That Matter\n\n" + quotes if not quotes.startswith("##") else quotes)

        summary = sections.get("summary", "").strip()
        if summary:
            parts.append(self._transition("So what’s the big picture?"))
            parts.append(summary)

        wtm = sections.get("what_this_means_for_you", "").strip()
        if wtm:
            parts.append(self._transition("Let’s make this practical."))
            parts.append(wtm)

        conclusion = sections.get("conclusion", "").strip()
        if conclusion:
            parts.append(self._transition("One honest caveat before we wrap up…"))
            parts.append(conclusion)

        tags = sections.get("tags", "").strip()
        if tags:
            parts.append(tags)

        # Final pass: remove duplicates and templated starts
        cleaned = []
        seen_starts = set()
        for block in parts:
            start_key = " ".join(block.strip().split()[:8]).lower()
            if start_key in seen_starts:
                continue
            if any(bp in block.lower() for bp in BANNED_PHRASES):
                continue
            seen_starts.add(start_key)
            cleaned.append(block)

        return "\n\n".join(cleaned) if cleaned else "No content generated."

    async def generate_blog_post(self, youtube_url: str) -> Dict[str, str]:
        print(f"[Orchestrator] Starting generation: {youtube_url}")
        raw_transcript = await fetch_transcript(youtube_url)
        transcript = self._enhance_if_thin(raw_transcript, youtube_url)

        chunks = chunk_text(transcript, 800)
        first = chunks[0] if chunks else transcript
        mid = chunks[len(chunks)//2] if chunks else transcript
        last = chunks[-1] if chunks else transcript

        # Route transcript slices by section
        routing_payloads = {
            "title": first,
            "intro": first,
            "context": first,
            "key_points_1": mid,
            "key_points_2": last if len(chunks) > 1 else mid,
            "quotes": transcript,
            "summary": transcript,
            "what_this_means_for_you": last,
            "conclusion": last,
            "seo": first,
            "tags": transcript[:1000],
        }

        # Minimum words per section (to avoid generic, too-short outputs)
        min_words = {
            "title": 1,
            "intro": 150,
            "context": 120,
            "key_points_1": 220,
            "key_points_2": 220,
            "quotes": 120,
            "summary": 150,
            "what_this_means_for_you": 150,
            "conclusion": 120,
            "seo": 1,
            "tags": 1,
        }

        # Run workers with retry + quality gates
        sections: Dict[str, str] = {}
        for name, worker in self.workers.items():
            try:
                # Temporarily patch each worker to accept routed payload by appending it
                # to the transcript to bias generation (workers read transcript only).
                routed_transcript = routing_payloads.get(name, transcript)
                out = await self._run_with_retry(worker, routed_transcript, min_words.get(name, 120))
                sections[name] = out
                print(f"[Orchestrator] Section {name}: {len(out or '')} chars")
            except Exception as e:
                print(f"[Orchestrator] Worker {name} error: {e}")
                sections[name] = ""

        # Assemble and return
        content = self._assemble(sections)

        stats = {
            "transcript_length": len(raw_transcript or ""),
            "enhanced_transcript_length": len(transcript or ""),
            "blog_length": len(content or ""),
            "word_count": len(content.split()),
            "success_rate": f"{sum(1 for v in sections.values() if v and len(v.strip())>20)}/{len(sections)}"
        }

        return {
            "content": content,
            "transcript": raw_transcript or "",
            "sections": sections,
            "metadata": {
                "description": "Humanized, narrative blog generated from YouTube content",
                "keywords": "machine learning, blog, video analysis, practical insights"
            },
            "stats": stats
        }
