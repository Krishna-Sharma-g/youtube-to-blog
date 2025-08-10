from __future__ import annotations
import asyncio
from typing import Dict, List
from pathlib import Path
import time
import os

from workers.implementations import (
    TitleWorker, IntroWorker, KeyPointsWorker, 
    QuotesWorker, SummaryWorker, ConclusionWorker, 
    SEOWorker, TagsWorker
)
from utils.youtube_processor import fetch_transcript

class BlogOrchestrator:
    """
    Orchestrates blog generation from YouTube videos.
    Fixed indentation and proper function bodies.
    """
    
    def __init__(self):
        """Initialize the orchestrator with all workers."""
        self.workers = [
            TitleWorker(),
            IntroWorker(), 
            KeyPointsWorker(),
            QuotesWorker(),
            SummaryWorker(),
            ConclusionWorker(),
            SEOWorker(),
            TagsWorker(),
        ]
        print(f"[Orchestrator] Initialized {len(self.workers)} workers")
    
    def _validate_real_transcript(self, transcript: str) -> bool:
        """Validate that we have real, meaningful content."""
        if not transcript or len(transcript.strip()) < 50:
            print("[Orchestrator] ❌ Content too short")
            return False
        
        transcript_lower = transcript.lower()
        
        # Only reject clear error cases
        hard_rejection_phrases = [
            'video processing error',
            'an error occurred while processing',
            'invalid video url format'
        ]
        
        for phrase in hard_rejection_phrases:
            if phrase in transcript_lower:
                print(f"[Orchestrator] ❌ Hard rejection: {phrase}")
                return False
        
        # Accept if we have ANY meaningful content
        content_indicators = [
            'video', 'title', 'description', 'content', 'analysis',
            'creator', 'channel', 'topic', 'subject', 'information',
            'discusses', 'covers', 'provides', 'insights', 'valuable'
        ]
        
        found_indicators = sum(1 for indicator in content_indicators if indicator in transcript_lower)
        
        if found_indicators >= 3:
            print(f"[Orchestrator] ✅ Content accepted ({found_indicators} indicators)")
            return True
        
        # Also accept based on length - if we have substantial text, it's probably good
        word_count = len(transcript.split())
        if word_count >= 50:
            print(f"[Orchestrator] ✅ Content accepted ({word_count} words)")
            return True
        
        print(f"[Orchestrator] ❌ Content quality insufficient")
        return False
    
    async def generate_blog_post(self, youtube_url: str) -> Dict[str, str]:
        """
        Generate a complete blog post from a YouTube URL.
        Main entry point for the orchestrator.
        """
        print(f"[Orchestrator] 🚀 Starting blog generation for: {youtube_url}")
        
        try:
            # Extract transcript
            transcript = await fetch_transcript(youtube_url)
            
            # Validate transcript
            if not self._validate_real_transcript(transcript):
                raise RuntimeError(
                    "Could not extract valid video content for analysis. "
                    "Please try a different video with:\n"
                    "• Clear speech and captions\n"
                    "• Educational or tutorial content\n"
                    "• At least 5 minutes of substantial content\n"
                    "• Public accessibility (not private/restricted)"
                )
            
            print(f"[Orchestrator] ✅ Processing {len(transcript)} chars of content")
            print(f"[Orchestrator] Running {len(self.workers)} workers...")
            
            # Process with workers
            tasks = []
            for worker in self.workers:
                task = asyncio.wait_for(
                    worker.generate(transcript), 
                    timeout=120  # 2 minutes per worker
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            sections = {}
            successful_workers = 0
            failed_workers = []
            
            for worker, result in zip(self.workers, results):
                worker_name = getattr(worker, 'name', worker.__class__.__name__.lower().replace('worker', ''))
                
                if isinstance(result, Exception):
                    print(f"[Orchestrator] ⚠️ Worker {worker_name} failed: {result}")
                    failed_workers.append(worker_name)
                    sections[worker_name] = f"<!-- {worker_name} analysis failed -->"
                else:
                    if result and len(result.strip()) > 50:
                        sections[worker_name] = result.strip()
                        successful_workers += 1
                        print(f"[Orchestrator] ✅ {worker_name}: {len(result)} chars")
                    else:
                        print(f"[Orchestrator] ⚠️ {worker_name}: empty result")
                        failed_workers.append(worker_name)
                        sections[worker_name] = f"<!-- {worker_name} returned empty content -->"
            
            # Require at least some workers to succeed
            if successful_workers < len(self.workers) // 2:
                raise RuntimeError(
                    f"Too many analysis workers failed ({len(failed_workers)}/{len(self.workers)}). "
                    f"Failed workers: {', '.join(failed_workers)}. "
                    f"This may indicate an issue with the OpenAI API or video content complexity."
                )
            
            # Assemble blog content
            blog_content = self._assemble_blog(sections)
            
            if len(blog_content.strip()) < 500:
                raise RuntimeError("Generated analysis is too short - indicates worker failures")
            
            # Prepare final result
            stats = {
                "transcript_length": len(transcript),
                "blog_length": len(blog_content),
                "word_count": len(blog_content.split()),
                "successful_workers": successful_workers,
                "failed_workers": failed_workers,
                "success_rate": f"{successful_workers}/{len(self.workers)}",
                "emergency_mode": False
            }
            
            print(f"[Orchestrator] ✅ Blog generated! {stats['word_count']} words")
            
            return {
                "content": blog_content,
                "transcript": transcript,
                "sections": sections,
                "metadata": self._extract_metadata(sections),
                "stats": stats
            }
            
        except Exception as e:
            print(f"[Orchestrator] ❌ Error: {str(e)}")
            raise e
    
    def _assemble_blog(self, sections: Dict[str, str]) -> str:
        """Assemble sections into final blog content."""
        section_order = [
            "title", "intro", "key_points", 
            "quotes", "summary", "conclusion", "tags"
        ]
        
        blog_parts = []
        
        for section_name in section_order:
            if section_name in sections:
                content = sections[section_name].strip()
                
                # Only include non-empty, real content
                if (content and 
                    not content.startswith("<!--") and
                    len(content) > 20 and
                    'failed' not in content.lower()):
                    blog_parts.append(content)
        
        if not blog_parts:
            raise RuntimeError("No valid content sections generated")
        
        return "\n\n".join(blog_parts)
    
    def _extract_metadata(self, sections: Dict[str, str]) -> Dict[str, str]:
        """Extract metadata from worker outputs."""
        metadata = {}
        
        try:
            if "seo" in sections and sections["seo"]:
                seo_content = sections["seo"]
                for line in seo_content.split('\n'):
                    if line.startswith('META_DESCRIPTION:'):
                        metadata['description'] = line.split(':', 1)[1].strip().strip('"')
                    elif line.startswith('KEYWORDS:'):
                        metadata['keywords'] = line.split(':', 1)[1].strip().strip('"')
        except Exception:
            pass
        
        # Ensure we have defaults
        if 'description' not in metadata:
            metadata['description'] = "Video content analysis and insights"
        if 'keywords' not in metadata:
            metadata['keywords'] = "video, content, analysis, insights"
        
        return metadata
