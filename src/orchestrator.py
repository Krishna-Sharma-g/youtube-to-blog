# Add this method to your BlogOrchestrator class
async def generate_blog_post(self, youtube_url: str) -> Dict[str, str]:
    """Generate blog post with retry logic for cloud reliability."""
    
    print(f"[Orchestrator] 🚀 Starting blog generation for: {youtube_url}")
    
    # Retry transcript extraction up to 3 times
    max_retries = 3
    retry_delay = 5  # seconds
    
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
            f"Last error: {last_error or 'Unknown error'}. "
            f"Please try a different video with clear speech and captions."
        )
        raise RuntimeError(error_msg)
    
    # Continue with normal blog generation...
    print(f"[Orchestrator] ✅ Proceeding with blog generation...")
    
    # Rest of your existing generate_blog_post code...
    tasks = [worker.generate(transcript) for worker in self.workers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # ... rest of your existing code
