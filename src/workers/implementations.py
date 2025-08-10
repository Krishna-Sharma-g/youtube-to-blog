from __future__ import annotations
from typing import Dict, Any
from .base import BlogWorker

class TitleWorker(BlogWorker):
    def __init__(self):
        super().__init__("title", max_tokens=100)
    
    def get_prompt(self, transcript: str, context: Dict[str, Any] = None) -> str:
        return f"""
Create an SEO-optimized, click-worthy title for a blog post based on this video transcript.

Requirements:
- 50-60 characters ideal for SEO
- Include main keyword/topic
- Make it compelling and specific
- Avoid clickbait, be accurate

Transcript excerpt: {transcript[:800]}

Return only the title, no quotes or extra text.
"""
    
    def format_output(self, raw_output: str) -> str:
        title = raw_output.strip().strip('"').strip("'")
        return f"# {title}\n"

class IntroWorker(BlogWorker):
    def __init__(self):
        super().__init__("intro", max_tokens=200)
    
    def get_prompt(self, transcript: str, context: Dict[str, Any] = None) -> str:
        return f"""
Write an engaging introduction paragraph for a blog post based on this video content.

Requirements:
- Hook the reader immediately
- Set context for what they'll learn
- 2-3 sentences maximum
- Connect with the audience

Transcript: {transcript[:1000]}

Write only the introduction paragraph.
"""
    
    def format_output(self, raw_output: str) -> str:
        return f"{raw_output.strip()}\n"

class KeyPointsWorker(BlogWorker):
    def __init__(self):
        super().__init__("key_points", max_tokens=500)
    
    def get_prompt(self, transcript: str, context: Dict[str, Any] = None) -> str:
        return f"""
Extract 3-5 key points from this video transcript and format them as blog sections.

Requirements:
- Each point should be a clear, actionable insight
- Use H2 headers (##) for each point
- Include 2-3 sentences explaining each point
- Focus on the most valuable takeaways

Transcript: {transcript}

Format:
## Key Point 1
Explanation...

## Key Point 2  
Explanation...
"""
    
    def format_output(self, raw_output: str) -> str:
        return f"{raw_output.strip()}\n"

class QuotesWorker(BlogWorker):
    def __init__(self):
        super().__init__("quotes", max_tokens=300)
    
    def get_prompt(self, transcript: str, context: Dict[str, Any] = None) -> str:
        return f"""
Find 2-3 powerful, quotable moments from this transcript.

Requirements:
- Choose impactful, memorable quotes
- Provide brief context for each
- Use markdown blockquote formatting
- Select quotes that capture key insights

Transcript: {transcript}

Format each as:
> "Exact quote here"

Brief context about why this matters...
"""
    
    def format_output(self, raw_output: str) -> str:
        return f"## Key Quotes\n\n{raw_output.strip()}\n"

class SummaryWorker(BlogWorker):
    def __init__(self):
        super().__init__("summary", max_tokens=200)
    
    def get_prompt(self, transcript: str, context: Dict[str, Any] = None) -> str:
        return f"""
Write a concise summary section that recaps the main points covered.

Requirements:
- 3-4 bullet points
- Each point should be one clear sentence
- Cover the essential takeaways
- Help readers remember key insights

Transcript: {transcript}

Use bullet point format with -
"""
    
    def format_output(self, raw_output: str) -> str:
        return f"## Summary\n\n{raw_output.strip()}\n"

class ConclusionWorker(BlogWorker):
    def __init__(self):
        super().__init__("conclusion", max_tokens=150)
    
    def get_prompt(self, transcript: str, context: Dict[str, Any] = None) -> str:
        return f"""
Write a strong conclusion that gives readers clear next steps.

Requirements:
- Reinforce the main value
- Provide 1-2 specific actions readers can take
- End with a forward-looking statement
- 2-3 sentences total

Based on transcript about: {transcript[:500]}

Write only the conclusion paragraph.
"""
    
    def format_output(self, raw_output: str) -> str:
        return f"## Conclusion\n\n{raw_output.strip()}\n"

class SEOWorker(BlogWorker):
    def __init__(self):
        super().__init__("seo", max_tokens=150)
    
    def get_prompt(self, transcript: str, context: Dict[str, Any] = None) -> str:
        return f"""
Generate SEO metadata for this blog post.

Requirements:
- Meta description: 150-160 characters, compelling summary
- 5-7 relevant keywords/phrases
- Focus on search intent

Transcript: {transcript[:800]}

Format:
META_DESCRIPTION: [description]
KEYWORDS: keyword1, keyword2, keyword3, etc.
"""
    
    def format_output(self, raw_output: str) -> str:
        # Extract meta info but don't include in main post
        return ""  # This will be used by the orchestrator for metadata

class TagsWorker(BlogWorker):
    def __init__(self):
        super().__init__("tags", max_tokens=100)
    
    def get_prompt(self, transcript: str, context: Dict[str, Any] = None) -> str:
        return f"""
Generate 5-8 relevant tags for this content.

Requirements:
- Mix of broad and specific topics
- Include primary subject area
- Consider target audience interests
- Use single words or short phrases

Transcript: {transcript[:600]}

Return only comma-separated tags.
"""
    
    def format_output(self, raw_output: str) -> str:
        tags = [tag.strip() for tag in raw_output.strip().split(',')]
        tag_line = " ".join([f"#{tag.replace(' ', '')}" for tag in tags if tag])
        return f"---\n**Tags:** {tag_line}\n"
