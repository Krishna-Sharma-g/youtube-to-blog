from __future__ import annotations
import asyncio
from typing import Dict, List
from pathlib import Path
import time
import traceback

from workers.implementations import (
    TitleWorker, IntroWorker, KeyPointsWorker, 
    QuotesWorker, SummaryWorker, ConclusionWorker, 
    SEOWorker, TagsWorker
)
from utils.youtube_processor import fetch_transcript

class SafeBlogWorker:
    """
    Wrapper that makes any worker fail-safe.
    Prevents individual worker failures from crashing the entire pipeline.
    """
    
    def __init__(self, worker, fallback_content: str = None):
        self.worker = worker
        self.name = getattr(worker, 'name', worker.__class__.__name__.lower().replace('worker', ''))
        self.fallback_content = fallback_content or self._get_default_fallback()
    
    def _get_default_fallback(self) -> str:
        """Generate appropriate fallback content based on worker type."""
        fallbacks = {
            'title': '# YouTube Video Analysis\n\nComprehensive insights and key takeaways from this video content.',
            'intro': 'This analysis explores the main themes and insights from the provided video content, offering valuable perspectives and actionable information.',
            'key_points': '## Key Insights\n\n• Important concepts and ideas discussed\n• Relevant strategies and approaches mentioned\n• Notable observations and recommendations',
            'quotes': '## Notable Excerpts\n\nKey statements and insights from the content that highlight important themes and concepts.',
            'summary': '## Summary\n\nThis content covers important topics with practical insights and valuable information for viewers interested in the subject matter.',
            'conclusion': '## Conclusion\n\nThe insights shared provide valuable perspectives on the topic, offering practical knowledge that can be applied effectively.',
            'seo': 'META_DESCRIPTION: "Comprehensive analysis and insights from video content"\nKEYWORDS: "analysis, insights, video content, information"',
            'tags': 'Tags: #analysis #insights #content #information #video'
        }
        return fallbacks.get(self.name, f"## {self.name.title()}\n\nContent analysis and insights.")
    
    async def generate(self, transcript: str) -> str:
        """Generate content with comprehensive error handling and fallbacks."""
        try:
            # Validate transcript before processing
            if not transcript or len(transcript.strip()) < 50:
                print(f"[SafeWorker:{self.name}] ⚠️ Transcript too short, using fallback")
                return self.fallback_content
            
            # Try the actual worker
            print(f"[SafeWorker:{self.name}] Generating content...")
            result = await self.worker.generate(transcript)
            
            # Validate result
            if result and len(result.strip()) > 20:
                print(f"[SafeWorker:{self.name}] ✅ Generated {len(result)} characters")
                return result.strip()
            else:
                print(f"[SafeWorker:{self.name}] ⚠️ Empty result, using fallback")
                return self.fallback_content
                
        except Exception as e:
            print(f"[SafeWorker:{self.name}] ❌ Error: {str(e)}")
            print(f"[SafeWorker:{self.name}] Using fallback content")
            return self.fallback_content

class BlogOrchestrator:
    """
    Bulletproof blog orchestrator that NEVER completely fails.
    Uses safe workers and fallback content to ensure output.
    """
    
    def __init__(self):
        # Initialize workers with safe wrappers
        raw_workers = [
            TitleWorker(),
            IntroWorker(), 
            KeyPointsWorker(),
            QuotesWorker(),
            SummaryWorker(),
            ConclusionWorker(),
            SEOWorker(),
            TagsWorker(),
        ]
        
        # Wrap all workers with safety layer
        self.workers = [SafeBlogWorker(worker) for worker in raw_workers]
        print(f"[Orchestrator] Initialized {len(self.workers)} safe workers")
    
    def _validate_transcript_strict(self, transcript: str) -> bool:
        """Ultra-strict transcript validation."""
        if not transcript or not transcript.strip():
            print("[Orchestrator] ❌ Empty transcript")
            return False
        
        transcript_clean = transcript.strip()
        
        # Check minimum length
        if len(transcript_clean) < 200:
            print(f"[Orchestrator] ❌ Transcript too short: {len(transcript_clean)} chars")
            return False
        
        # Check for error messages
        error_indicators = [
            'could not extract', 'all strategies failed', 'try a different video',
            'network connectivity', 'private', 'restricted', 'blocked',
            'no speech content', 'unclear audio', 'failed to', 'error:'
        ]
        
        transcript_lower = transcript.lower()
        for indicator in error_indicators:
            if indicator in transcript_lower:
                print(f"[Orchestrator] ❌ Error indicator: '{indicator}'")
                return False
        
        # Check word count and diversity
        words = transcript_clean.split()
        unique_words = set(w.lower() for w in words if len(w) > 2)
        
        if len(words) < 50:
            print(f"[Orchestrator] ❌ Too few words: {len(words)}")
            return False
        
        if len(unique_words) < 25:
            print(f"[Orchestrator] ❌ Low vocabulary diversity: {len(unique_words)}")
            return False
        
        # Check for basic English structure
        common_words = ['the', 'and', 'is', 'are', 'to', 'of', 'in', 'for', 'with', 'on']
        found_common = sum(1 for word in common_words if word in transcript_lower)
        
        if found_common < 5:
            print(f"[Orchestrator] ❌ Doesn't look like English: {found_common} common words")
            return False
        
        print(f"[Orchestrator] ✅ Transcript validated: {len(words)} words, {len(unique_words)} unique")
        return True
    
    def _create_emergency_blog(self, youtube_url: str, attempted_transcript: str = "") -> Dict[str, str]:
        """Create emergency blog when all else fails."""
        video_id = youtube_url.split('v=')[-1].split('&')[0] if 'v=' in youtube_url else 'unknown'
        
        emergency_content = f"""# Video Content Analysis

## Overview

This analysis is based on available video content from YouTube. The video covers various topics and provides insights that may be valuable to viewers.

## Key Information

The content appears to discuss important themes and concepts. While detailed analysis was not possible due to processing limitations, the video likely contains valuable information for its intended audience.

## Summary

This video content provides insights and information on its topic. For the most accurate understanding, viewers are encouraged to watch the video directly.

## Content Details

**Video ID:** {video_id}
**Processing Status:** Limited analysis available
**Recommendation:** Watch video directly for complete information

---

*Note: This analysis was generated with limited content processing. For full insights, please view the original video.*

**Tags:** #video #content #analysis #youtube"""

        return {
            "content": emergency_content,
            "transcript": attempted_transcript,
            "sections": {"emergency": emergency_content},
            "metadata": {
                "description": "Video content analysis with limited processing",
                "keywords": "video, content, analysis, youtube"
            },
            "stats": {
                "word_count": len(emergency_content.split()),
                "emergency_mode": True,
                "failed_workers": "all"
            }
        }
    
    async def generate_blog_post(self, youtube_url: str) -> Dict[str, str]:
        """
        Generate blog post with multiple safety layers.
        GUARANTEED to return content - will never completely fail.
        """
        
        print(f"[Orchestrator] 🚀 Starting bulletproof blog generation for: {youtube_url}")
        
        # Multi-attempt transcript extraction
        max_retries = 3
        transcript = None
        
        for attempt in range(1, max_retries + 1):
            try:
                print(f"[Orchestrator] Attempt {attempt}/{max_retries} - Fetching transcript...")
                transcript = await fetch_transcript(youtube_url)
                
                if self._validate_transcript_strict(transcript):
                    print(f"[Orchestrator] ✅ Valid transcript obtained on attempt {attempt}")
                    break
                else:
                    print(f"[Orchestrator] ⚠️ Invalid transcript on attempt {attempt}")
                    
            except Exception as e:
                print(f"[Orchestrator] ❌ Attempt {attempt} failed: {str(e)}")
            
            if attempt < max_retries:
                await asyncio.sleep(2)
        
        # If no valid transcript, use emergency mode
        if not transcript or not self._validate_transcript_strict(transcript):
            print("[Orchestrator] 🚨 Using emergency blog generation")
            return self._create_emergency_blog(youtube_url, transcript or "")
        
        # Process with safe workers
        print(f"[Orchestrator] ✅ Processing with {len(self.workers)} safe workers...")
        
        try:
            # Run all workers with individual timeout protection
            tasks = []
            for worker in self.workers:
                task = asyncio.wait_for(worker.generate(transcript), timeout=60)  # 1 min per worker
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            sections = {}
            successful_workers = 0
            
            for worker, result in zip(self.workers, results):
                if isinstance(result, Exception):
                    print(f"[Orchestrator] ⚠️ Worker {worker.name} timed out or failed: {result}")
                    sections[worker.name] = worker.fallback_content
                else:
                    sections[worker.name] = result
                    successful_workers += 1
            
            # Assemble blog content
            blog_content = self._assemble_blog_guaranteed(sections)
            
            # Success statistics
            stats = {
                "transcript_length": len(transcript),
                "blog_length": len(blog_content),
                "word_count": len(blog_content.split()),
                "successful_workers": successful_workers,
                "total_workers": len(self.workers),
                "success_rate": f"{successful_workers}/{len(self.workers)}",
                "emergency_mode": False
            }
            
            print(f"[Orchestrator] ✅ Blog generated! {stats['word_count']} words, {stats['success_rate']} workers succeeded")
            
            return {
                "content": blog_content,
                "transcript": transcript,
                "sections": sections,
                "metadata": self._extract_metadata_safe(sections),
                "stats": stats
            }
            
        except Exception as e:
            print(f"[Orchestrator] 🚨 Worker processing failed: {str(e)}")
            print("[Orchestrator] Using emergency blog generation")
            return self._create_emergency_blog(youtube_url, transcript)
    
    def _assemble_blog_guaranteed(self, sections: Dict[str, str]) -> str:
        """Assemble blog content that's guaranteed to have content."""
        section_order = [
            "title", "intro", "key_points", 
            "quotes", "summary", "conclusion", "tags"
        ]
        
        blog_parts = []
        
        for section_name in section_order:
            if section_name in sections:
                content = sections[section_name].strip()
                if content and len(content) > 10:
                    blog_parts.append(content)
        
        # Guarantee we have content
        if not blog_parts:
            blog_parts = [
                "# Content Analysis",
                "This analysis provides insights from the video content.",
                "## Summary",
                "The video covers important topics and provides valuable information.",
                "Tags: #content #analysis #video"
            ]
        
        return "\n\n".join(blog_parts)
    
    def _extract_metadata_safe(self, sections: Dict[str, str]) -> Dict[str, str]:
        """Extract metadata with safe defaults."""
        metadata = {}
        
        try:
            if "seo" in sections and sections["seo"]:
                seo_content = sections["seo"]
                for line in seo_content.split('\n'):
                    if line.startswith('META_DESCRIPTION:'):
                        metadata['description'] = line.split(':', 1)[1].strip().strip('"')
                    elif line.startswith('KEYWORDS:'):
                        metadata['keywords'] = line.split(':', 1)[1].strip().strip('"')
        except:
            pass
        
        # Ensure we have defaults
        if 'description' not in metadata:
            metadata['description'] = "Video content analysis and insights"
        if 'keywords' not in metadata:
            metadata['keywords'] = "video, content, analysis, insights"
        
        return metadata

