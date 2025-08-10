from __future__ import annotations
import asyncio
from typing import Dict, List
from pathlib import Path
import time

from workers.implementations import (
    TitleWorker, IntroWorker, KeyPointsWorker, 
    QuotesWorker, SummaryWorker, ConclusionWorker, 
    SEOWorker, TagsWorker
)
from utils.youtube_processor import fetch_transcript

class BlogOrchestrator:
    """
    REAL content analysis orchestrator - no more generic content!
    """
    
    def __init__(self):
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
    
    def _validate_real_transcript(self, transcript: str) -> bool:
        """Validate we have REAL content, not error messages or generic text."""
        if not transcript or len(transcript.strip()) < 200:
            print("[Orchestrator] ❌ Transcript too short")
            return False
        
        # Check for error indicators
        error_indicators = [
            'could not extract', 'failed to extract', 'this video may',
            'please try a different', 'be private', 'age-restricted',
            'no speech content', 'disabled captions'
        ]
        
        transcript_lower = transcript.lower()
        for indicator in error_indicators:
            if indicator in transcript_lower:
                print(f"[Orchestrator] ❌ Error detected: {indicator}")
                return False
        
        # Check for real content indicators
        real_content_indicators = [
            # Should have natural speech patterns
            ' and ', ' but ', ' so ', ' because ', ' that ', ' this ',
            # Should have some specificity
            ' i ', ' we ', ' you ', ' they ', ' my ', ' our ',
            # Should have some content depth
            '?', '!', ',', ';', ':',
        ]
        
        indicator_count = sum(1 for indicator in real_content_indicators if indicator in transcript_lower)
        
        if indicator_count < 15:  # Should have natural speech patterns
            print(f"[Orchestrator] ❌ Doesn't look like natural content: {indicator_count} indicators")
            return False
        
        # Check for diversity in content
        words = transcript_lower.split()
        unique_words = set(words)
        
        if len(unique_words) < 50:
            print(f"[Orchestrator] ❌ Low vocabulary diversity: {len(unique_words)}")
            return False
        
        print(f"[Orchestrator] ✅ Real content validated: {len(words)} words, {len(unique_words)} unique")
        return True
    
    async def generate_blog_post(self, youtube_url: str) -> Dict[str, str]:
        """Generate blog with REAL video analysis."""
        
        print(f"[Orchestrator] 🚀 Starting REAL content analysis for: {youtube_url}")
        
        # Extract transcript with validation
        transcript = await fetch_transcript(youtube_url)
        
        # Strict validation - reject if not real content
        if not self._validate_real_transcript(transcript):
            raise RuntimeError(
                "Could not extract valid video content for analysis. "
                "Please try a different video with:\n"
                "• Clear speech and captions\n"
                "• Educational or tutorial content\n"
                "• At least 5 minutes of substantial content\n"
                "• Public accessibility (not private/restricted)"
            )
        
        print(f"[Orchestrator] ✅ Processing {len(transcript)} chars of REAL content")
        print(f"[Orchestrator] Running {len(self.workers)} workers for analysis...")
        
        # Test OpenAI connection first
        try:
            from utils.openai_client import test_openai
            connection_ok = await test_openai()
            if not connection_ok:
                raise RuntimeError("OpenAI connection failed - check API key")
        except Exception as e:
            raise RuntimeError(f"OpenAI setup error: {str(e)}")
        
        # Process with real workers
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
                # Don't use fallback - better to fail than give generic content
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
        
        # Require at least half the workers to succeed
        if successful_workers < len(self.workers) // 2:
            raise RuntimeError(
                f"Too many analysis workers failed ({len(failed_workers)}/{len(self.workers)}). "
                f"Failed workers: {', '.join(failed_workers)}. "
                f"This may indicate an issue with the OpenAI API or video content complexity."
            )
        
        # Assemble blog
        blog_content = self._assemble_real_blog(sections)
        
        if len(blog_content.strip()) < 500:
            raise RuntimeError("Generated analysis is too short - indicates worker failures")
        
        stats = {
            "transcript_length": len(transcript),
            "blog_length": len(blog_content),
            "word_count": len(blog_content.split()),
            "successful_workers": successful_workers,
            "failed_workers": failed_workers,
            "success_rate": f"{successful_workers}/{len(self.workers)}"
        }
        
        print(f"[Orchestrator] ✅ REAL analysis complete! {stats['word_count']} words")
        
        return {
            "content": blog_content,
            "transcript": transcript,
            "sections": sections,
            "metadata": self._extract_metadata(sections),
            "stats": stats
        }
    
    def _assemble_real_blog(self, sections: Dict[str, str]) -> str:
        """Assemble blog ensuring we have real content."""
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
        """Extract metadata from sections."""
        metadata = {}
        
        if "seo" in sections and sections["seo"]:
            seo_content = sections["seo"]
            for line in seo_content.split('\n'):
                if line.startswith('META_DESCRIPTION:'):
                    metadata['description'] = line.split(':', 1)[1].strip().strip('"')
                elif line.startswith('KEYWORDS:'):
                    metadata['keywords'] = line.split(':', 1)[11].strip().strip('"')
        
        return metadata
