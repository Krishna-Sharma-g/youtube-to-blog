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
    🚀 UNIVERSAL VERSION - Works with any YouTube video!
    🛡️ BULLETPROOF - Strict validation prevents placeholder content
    ⚡ OPTIMIZED - Fast parallel processing
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
        """
        Strict transcript validation to prevent placeholder content.
        Returns True only if transcript is meaningful and complete.
        """
        if not transcript or not transcript.strip():
            print("[Orchestrator] ❌ Empty transcript")
            return False
        
        # Check minimum length - reduced for faster processing
        transcript_clean = transcript.strip()
        if len(transcript_clean) < 100:
            print(f"[Orchestrator] ❌ Transcript too short: {len(transcript_clean)} chars")
            return False
        
        # Check for error indicators
        error_markers = [
            'all extraction strategies failed',
            'video may be private',
            'no speech content', 
            'audio quality',
            'error:', 'failed:', 'cannot', 'unable to',
            'transcript unavailable', 'not available', 
            'extraction failed', 'download failed',
            'missing required tools', 'transcription failed',
            'no text was extracted', 'generic template',
            'since i cannot access', 'placeholder',
            'fill in the details', 'you can provide',
            'i cannot extract', 'template', 'unavailable'
        ]
        
        transcript_lower = transcript.lower()
        for marker in error_markers:
            if marker in transcript_lower:
                print(f"[Orchestrator] ❌ Error marker found: '{marker}'")
                return False
        
        # Check for meaningful content structure
        words = transcript_lower.split()
        unique_words = set(words)
        
        # Very lenient requirements for universal compatibility
        if len(words) < 20:
            print(f"[Orchestrator] ❌ Too few words: {len(words)}")
            return False
            
        if len(unique_words) < 15:
            print(f"[Orchestrator] ❌ Insufficient vocabulary: {len(unique_words)} unique words")
            return False
        
        # Check for basic English indicators
        common_words = ['the', 'and', 'is', 'are', 'was', 'were', 'to', 'of', 'in', 'for']
        common_count = sum(1 for word in common_words if word in transcript_lower)
        
        if common_count < 3:
            print(f"[Orchestrator] ❌ Doesn't look like English content: {common_count} common words")
            return False
        
        print(f"[Orchestrator] ✅ Transcript validated: {len(words)} words, {len(unique_words)} unique")
        return True
    
    async def generate_blog_post(self, youtube_url: str) -> Dict[str, str]:
        """
        Generate complete blog post with universal compatibility.
        Guarantees real content or fails with clear error messages.
        """
        
        print(f"[Orchestrator] 🚀 Starting blog generation for: {youtube_url}")
        
        try:
            # Fetch transcript using universal processor
            transcript = await fetch_transcript(youtube_url)
            
        except Exception as e:
            error_msg = f"Failed to fetch transcript: {str(e)}"
            print(f"[Orchestrator] ❌ {error_msg}")
            raise RuntimeError(error_msg)
        
        # CRITICAL: Validate transcript before proceeding
        if not self._validate_transcript(transcript):
            # Determine specific failure reason
            if not transcript or len(transcript.strip()) < 50:
                error_msg = (
                    "No meaningful content could be extracted from this video. "
                    "This might be because:\n"
                    "• The video is private or region-restricted\n"
                    "• The video contains no speech (music only)\n"
                    "• The video has very poor audio quality\n"
                    "• The video is too short to extract meaningful content"
                )
            elif len(transcript.strip()) < 100:
                error_msg = (
                    f"Transcript too short ({len(transcript)} characters) for meaningful blog generation. "
                    f"Please try a longer video with more substantial content."
                )
            elif any(marker in transcript.lower() for marker in ['error', 'failed', 'cannot', 'unavailable']):
                error_msg = (
                    "Transcript extraction encountered technical issues. "
                    "Please try:\n"
                    "• A different video with clearer audio\n"
                    "• Updating yt-dlp: brew upgrade yt-dlp\n"
                    "• Checking your internet connection"
                )
            else:
                error_msg = (
                    "The extracted content doesn't appear to be suitable for blog generation. "
                    "Please try a video with clear, substantial speech content."
                )
            
            print(f"[Orchestrator] ❌ Validation failed")
            raise RuntimeError(error_msg)
        
        print(f"[Orchestrator] ✅ Transcript validated! Running {len(self.workers)} workers in parallel...")
        
        try:
            # Run all workers concurrently with the VALIDATED transcript
            tasks = [
                worker.generate(transcript) 
                for worker in self.workers
            ]
            
            # Use return_exceptions=True to handle individual worker failures
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and identify failures
            sections = {}
            failed_workers = []
            
            for worker, result in zip(self.workers, results):
                if isinstance(result, Exception):
                    print(f"[Orchestrator] ⚠️ Worker {worker.name} failed: {result}")
                    failed_workers.append(worker.name)
                    # Create minimal fallback content
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
        """
        Assemble sections into final blog post with quality filtering.
        """
        # Define the order of sections
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
                        'error:', 'failed:', 'cannot extract', 'placeholder',
                        'generic template', 'since i cannot access'
                    ])):
                    blog_parts.append(content)
        
        if not blog_parts:
            raise RuntimeError("No valid sections were generated - all workers failed")
        
        # Join with double newlines for proper Markdown spacing
        return "\n\n".join(blog_parts)
    
    def _extract_metadata(self, sections: Dict[str, str]) -> Dict[str, str]:
        """
        Extract SEO metadata from worker outputs.
        """
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
        """
        Save generated blog post to file with optional metadata.
        """
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
                f"<!-- Success rate: {stats.get('success_rate', 'unknown')} -->",
                f"<!-- Transcript length: {stats.get('transcript_length', 'unknown')} chars -->"
            ])
        
        final_content = "\n".join(content_parts)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_content)
        
        print(f"[Orchestrator] 💾 Blog post saved to: {output_path.absolute()}")
        print(f"[Orchestrator] 📊 Final size: {len(final_content)} characters")
