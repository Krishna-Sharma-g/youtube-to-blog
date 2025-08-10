from __future__ import annotations
import asyncio
from typing import Dict, List
from pathlib import Path

from workers.implementations import (
    TitleWorker, IntroWorker, KeyPointsWorker, 
    QuotesWorker, SummaryWorker, ConclusionWorker, 
    SEOWorker, TagsWorker
)
from utils.youtube_processor import fetch_transcript

class BlogOrchestrator:
    """
    Coordinates all workers to generate a complete blog post.
    🚀 CLOUD-OPTIMIZED with retry logic and proper error handling
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
    
    def _validate_transcript(self, transcript: str) -> bool:
        """Validate transcript quality to prevent placeholder content."""
        if not transcript or not transcript.strip():
            print("[Orchestrator] ❌ Empty transcript")
            return False
        
        # Check minimum length
        transcript_clean = transcript.strip()
        if len(transcript_clean) < 100:
            print(f"[Orchestrator] ❌ Transcript too short: {len(transcript_clean)} chars")
            return False
        
        # Check for error indicators
        error_markers = [
            'could not extract content', 'all strategies failed',
            'video is private', 'no speech content', 
            'network connectivity issues', 'try a different video',
            'error:', 'failed:', 'cannot', 'unable to',
            'transcript unavailable', 'extraction failed',
        ]
        
        transcript_lower = transcript.lower()
        for marker in error_markers:
            if marker in transcript_lower:
                print(f"[Orchestrator] ❌ Error marker found: '{marker}'")
                return False
        
        # Check for meaningful content structure
        words = transcript_lower.split()
        if len(words) < 30:
            print(f"[Orchestrator] ❌ Too few words: {len(words)}")
            return False
        
        print(f"[Orchestrator] ✅ Transcript validated: {len(words)} words")
        return True
    
    async def generate_blog_post(self, youtube_url: str) -> Dict[str, str]:
        """
        Generate complete blog post with retry logic for cloud reliability.
        🌐 GUARANTEED to work in Streamlit Cloud environment!
        """
        
        print(f"[Orchestrator] 🚀 Starting blog generation for: {youtube_url}")
        
        # Retry transcript extraction up to 3 times
        max_retries = 3
        retry_delay = 3  # seconds
        
        transcript = None
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                print(f"[Orchestrator] Attempt {attempt}/{max_retries} - Fetching transcript...")
                transcript = await fetch_transcript(youtube_url)
                
                # Validate transcript
                if self._validate_transcript(transcript):
                    print(f"[Orchestrator] ✅ Transcript validated on attempt {attempt}")
                    break
                else:
                    last_error = f"Invalid transcript on attempt {attempt}"
                    print(f"[Orchestrator] ❌ {last_error}")
                    
            except Exception as e:
                last_error = str(e)
                print(f"[Orchestrator] ❌ Attempt {attempt} failed: {last_error}")
            
            # Wait before retry (except on last attempt)
            if attempt < max_retries:
                print(f"[Orchestrator] ⏳ Waiting {retry_delay}s before retry...")
                await asyncio.sleep(retry_delay)
        
        # Check if we got a valid transcript
        if not transcript or not self._validate_transcript(transcript):
            error_msg = (
                f"Failed to extract valid transcript after {max_retries} attempts. "
                f"This video may not be suitable for blog generation. "
                f"Please try:\n\n"
                f"• A different video with clear speech\n"
                f"• An educational or tutorial video\n"
                f"• A video that has captions/subtitles\n"
                f"• A longer video with substantial content"
            )
            raise RuntimeError(error_msg)
        
        print(f"[Orchestrator] ✅ Proceeding with blog generation...")
        print(f"[Orchestrator] Running {len(self.workers)} workers in parallel...")
        
        try:
            # Run all workers concurrently with the VALIDATED transcript
            tasks = [
                worker.generate(transcript) 
                for worker in self.workers
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and identify failures
            sections = {}
            failed_workers = []
            
            for worker, result in zip(self.workers, results):
                if isinstance(result, Exception):
                    print(f"[Orchestrator] ⚠️ Worker {worker.name} failed: {result}")
                    failed_workers.append(worker.name)
                    sections[worker.name] = f"<!-- {worker.name} section failed to generate -->"
                else:
                    sections[worker.name] = result.strip() if result else ""
            
            # Check if too many workers failed
            if len(failed_workers) > len(self.workers) // 2:
                error_msg = f"Too many workers failed ({len(failed_workers)}/{len(self.workers)}): {', '.join(failed_workers)}"
                print(f"[Orchestrator] ❌ {error_msg}")
                raise RuntimeError(error_msg)
            
            # Assemble final blog post
            blog_content = self._assemble_blog(sections)
            
            # Final quality check
            if len(blog_content.strip()) < 300:
                error_msg = "Generated blog content is too short - indicates systematic failure"
                print(f"[Orchestrator] ❌ {error_msg}")
                raise RuntimeError(error_msg)
            
            # Success! Return complete blog data
            stats = {
                "transcript_length": len(transcript),
                "blog_length": len(blog_content),
                "word_count": len(blog_content.split()),
                "failed_workers": failed_workers,
                "success_rate": f"{len(self.workers) - len(failed_workers)}/{len(self.workers)}"
            }
            
            print(f"[Orchestrator] ✅ Blog generation complete! {stats['word_count']} words, {stats['success_rate']} workers succeeded")
            
            return {
                "content": blog_content,
                "transcript": transcript,
                "sections": sections,
                "metadata": self._extract_metadata(sections),
                "stats": stats
            }
            
        except Exception as e:
            error_msg = f"Blog generation failed during worker processing: {str(e)}"
            print(f"[Orchestrator] ❌ {error_msg}")
            raise RuntimeError(error_msg)
    
    def _assemble_blog(self, sections: Dict[str, str]) -> str:
        """Assemble sections into final blog post with quality filtering."""
        section_order = [
            "title", "intro", "key_points", 
            "quotes", "summary", "conclusion", "tags"
        ]
        
        blog_parts = []
        
        for section_name in section_order:
            if section_name in sections:
                content = sections[section_name].strip()
                
                # Skip empty sections or error placeholders
                if (content and 
                    not content.startswith("<!--") and
                    len(content) > 10 and
                    not any(error in content.lower() for error in [
                        'error:', 'failed:', 'cannot extract', 'placeholder'
                    ])):
                    blog_parts.append(content)
        
        if not blog_parts:
            raise RuntimeError("No valid sections were generated - all workers failed")
        
        return "\n\n".join(blog_parts)
    
    def _extract_metadata(self, sections: Dict[str, str]) -> Dict[str, str]:
        """Extract SEO metadata from worker outputs."""
        metadata = {}
        
        if "seo" in sections and sections["seo"].strip():
            seo_content = sections["seo"]
            lines = seo_content.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('META_DESCRIPTION:'):
                    metadata['description'] = line.split(':', 1)[1].strip().strip('"')
                elif line.startswith('KEYWORDS:'):
                    metadata['keywords'] = line.split(':', 1)[1].strip().strip('"')
        
        return metadata
    
    async def save_blog_post(self, blog_data: Dict[str, str], output_path: Path) -> None:
        """Save generated blog post to file with optional metadata."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        content_parts = []
        
        # Add frontmatter if metadata exists
        metadata = blog_data.get("metadata", {})
        if metadata:
            content_parts.append("---")
            if "description" in metadata:
                content_parts.append(f'description: "{metadata["description"]}"')
            if "keywords" in metadata:
                content_parts.append(f'keywords: "{metadata["keywords"]}"')
            content_parts.append("---")
            content_parts.append("")
        
        # Add main content
        content_parts.append(blog_data["content"])
        
        # Add generation stats as comment
        if "stats" in blog_data:
            stats = blog_data["stats"]
            content_parts.extend([
                "",
                "<!-- Generated by YouTube Blog Generator -->",
                f"<!-- Word count: {stats.get('word_count', 'unknown')} -->",
                f"<!-- Success rate: {stats.get('success_rate', 'unknown')} -->"
            ])
        
        final_content = "\n".join(content_parts)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_content)
        
        print(f"[Orchestrator] 💾 Blog post saved to: {output_path.absolute()}")
