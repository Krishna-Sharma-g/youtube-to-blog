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

class BlogOrchestrator:
    """
    Robust orchestrator with comprehensive debugging and error handling.
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
        print(f"[Orchestrator] ✅ Initialized {len(self.workers)} workers")
    
    def _validate_real_transcript(self, transcript: str) -> bool:
        """Strict transcript validation with detailed logging."""
        print(f"[Orchestrator] Validating transcript...")
        
        if not transcript:
            print("[Orchestrator] ❌ Transcript is None or empty")
            return False
        
        transcript_clean = transcript.strip()
        print(f"[Orchestrator] Transcript length after cleaning: {len(transcript_clean)}")
        
        if len(transcript_clean) < 200:
            print(f"[Orchestrator] ❌ Transcript too short: {len(transcript_clean)} chars")
            return False
        
        # Check for error messages in transcript
        error_markers = [
            'could not extract', 'failed to extract', 'error occurred',
            'try a different video', 'video may be private', 'no speech content'
        ]
        
        transcript_lower = transcript_clean.lower()
        for marker in error_markers:
            if marker in transcript_lower:
                print(f"[Orchestrator] ❌ Error marker found: '{marker}'")
                return False
        
        # Check for substantial content
        words = transcript_clean.split()
        unique_words = set(w.lower() for w in words if len(w) > 3)
        
        print(f"[Orchestrator] Word count: {len(words)}, unique words: {len(unique_words)}")
        
        if len(words) < 100:
            print(f"[Orchestrator] ❌ Too few words: {len(words)}")
            return False
        
        if len(unique_words) < 30:
            print(f"[Orchestrator] ❌ Low vocabulary diversity: {len(unique_words)}")
            return False
        
        print(f"[Orchestrator] ✅ Transcript validation passed")
        return True
    
    async def generate_blog_post(self, youtube_url: str) -> Dict[str, str]:
        """Generate blog post with comprehensive error tracking."""
        print(f"[Orchestrator] 🚀 Starting blog generation for: {youtube_url}")
        
        # Step 1: Extract transcript with validation
        print(f"[Orchestrator] Step 1: Extracting transcript...")
        transcript = await fetch_transcript(youtube_url)
        
        print(f"[Orchestrator] Raw transcript length: {len(transcript) if transcript else 0}")
        if transcript:
            print(f"[Orchestrator] Transcript preview (first 300 chars):")
            print(f"'{transcript[:300]}...'")
        
        # Step 2: Validate transcript
        print(f"[Orchestrator] Step 2: Validating transcript...")
        if not self._validate_real_transcript(transcript):
            error_msg = (
                "❌ Transcript validation failed. The video content could not be properly extracted. "
                "Please try:\n"
                "• A video with clear speech and captions\n"
                "• Educational or tutorial content\n"
                "• Videos longer than 5 minutes\n"
                "• Popular videos from major creators"
            )
            print(f"[Orchestrator] {error_msg}")
            raise RuntimeError(error_msg)
        
        # Step 3: Process with workers
        print(f"[Orchestrator] Step 3: Processing with {len(self.workers)} workers...")
        
        sections = {}
        successful_workers = 0
        failed_workers = []
        worker_errors = {}
        
        # Process each worker individually with detailed tracking
        for i, worker in enumerate(self.workers, 1):
            worker_name = worker.name
            print(f"\n[Orchestrator] Processing worker {i}/{len(self.workers)}: {worker_name}")
            
            try:
                # Call worker with timeout
                print(f"[Orchestrator] Calling {worker_name}.generate()...")
                start_time = time.time()
                
                result = await asyncio.wait_for(
                    worker.generate(transcript), 
                    timeout=180  # 3 minutes per worker
                )
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                # Validate worker result
                if result and len(result.strip()) > 50:
                    # Check if it's not just fallback content
                    if "As an ML researcher, let me break down what we discovered" not in result:
                        sections[worker_name] = result.strip()
                        successful_workers += 1
                        print(f"[Orchestrator] ✅ {worker_name} SUCCESS: {len(result)} chars in {processing_time:.1f}s")
                        print(f"[Orchestrator] Preview: {result[:100]}...")
                    else:
                        failed_workers.append(worker_name)
                        worker_errors[worker_name] = "Returned fallback content"
                        print(f"[Orchestrator] ❌ {worker_name} returned fallback content")
                else:
                    failed_workers.append(worker_name)
                    worker_errors[worker_name] = "Empty or too short result"
                    print(f"[Orchestrator] ❌ {worker_name} returned empty/short result")
                    
            except asyncio.TimeoutError:
                failed_workers.append(worker_name)
                worker_errors[worker_name] = "Timeout after 3 minutes"
                print(f"[Orchestrator] ❌ {worker_name} TIMEOUT")
                
            except Exception as e:
                failed_workers.append(worker_name)
                worker_errors[worker_name] = str(e)
                print(f"[Orchestrator] ❌ {worker_name} EXCEPTION: {e}")
                print(f"[Orchestrator] Traceback: {traceback.format_exc()}")
        
        # Step 4: Analyze results
        print(f"\n[Orchestrator] Step 4: Analyzing results...")
        print(f"[Orchestrator] Successful workers: {successful_workers}/{len(self.workers)}")
        print(f"[Orchestrator] Failed workers: {failed_workers}")
        
        if successful_workers == 0:
            error_details = "\n".join([f"• {name}: {error}" for name, error in worker_errors.items()])
            error_msg = (
                f"❌ All {len(self.workers)} workers failed to generate content.\n\n"
                f"Detailed errors:\n{error_details}\n\n"
                f"This usually indicates:\n"
                f"• OpenAI API key issues\n"
                f"• Network connectivity problems\n"
                f"• API rate limiting or billing issues"
            )
            print(f"[Orchestrator] {error_msg}")
            raise RuntimeError(error_msg)
        
        if successful_workers < len(self.workers) // 2:
            print(f"[Orchestrator] ⚠️ Warning: Only {successful_workers}/{len(self.workers)} workers succeeded")
        
        # Step 5: Assemble blog
        print(f"[Orchestrator] Step 5: Assembling blog...")
        blog_content = self._assemble_blog(sections)
        
        if len(blog_content.strip()) < 500:
            raise RuntimeError("Generated blog content is too short - indicates systematic failure")
        
        # Success!
        stats = {
            "transcript_length": len(transcript),
            "blog_length": len(blog_content),
            "word_count": len(blog_content.split()),
            "successful_workers": successful_workers,
            "failed_workers": failed_workers,
            "worker_errors": worker_errors,
            "success_rate": f"{successful_workers}/{len(self.workers)}"
        }
        
        print(f"[Orchestrator] ✅ Blog generation COMPLETE!")
        print(f"[Orchestrator] Final stats: {stats['word_count']} words, {stats['success_rate']} workers succeeded")
        
        return {
            "content": blog_content,
            "transcript": transcript,
            "sections": sections,
            "metadata": {},
            "stats": stats
        }
    
    def _assemble_blog(self, sections: Dict[str, str]) -> str:
        """Assemble blog content with quality filtering."""
        section_order = [
            "title", "intro", "key_points", 
            "quotes", "summary", "conclusion", "tags"
        ]
        
        blog_parts = []
        
        for section_name in section_order:
            if section_name in sections:
                content = sections[section_name].strip()
                
                # Only include real content (not fallback or error messages)
                if (content and 
                    len(content) > 20 and
                    not content.startswith("<!--") and
                    "As an ML researcher, let me break down" not in content):
                    blog_parts.append(content)
                    print(f"[Orchestrator] Including {section_name}: {len(content)} chars")
                else:
                    print(f"[Orchestrator] Skipping {section_name}: invalid content")
        
        if not blog_parts:
            return "No valid content sections were generated."
        
        return "\n\n".join(blog_parts)

