from __future__ import annotations
import requests
import json
from typing import List, Dict
import streamlit as st
import os
import time

class BaseWorker:
    """Base worker using requests instead of aiohttp."""
    
    def __init__(self, name: str):
        self.name = name
    
    def _call_openai_sync(self, messages: List[Dict], max_tokens: int = 1000) -> str:
        """Synchronous OpenAI API call using requests."""
        try:
            # Get API key
            api_key = None
            try:
                api_key = st.secrets["OPENAI_API_KEY"]
            except:
                api_key = os.getenv("OPENAI_API_KEY")
            
            if not api_key or not api_key.startswith("sk-"):
                raise Exception("OpenAI API key not found or invalid")
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return content.strip()
            else:
                raise Exception(f"OpenAI API Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"[{self.name}] OpenAI call failed: {e}")
            raise e
    
    async def generate(self, transcript: str) -> str:
        """Generate content with fallback."""
        try:
            if not transcript or len(transcript) < 50:
                return self._get_fallback_content()
            
            # Run sync function in thread to make it "async"
            import asyncio
            return await asyncio.to_thread(self._generate_content_sync, transcript)
            
        except Exception as e:
            print(f"[{self.name}] Generation failed: {e}")
            return self._get_fallback_content()
    
    def _generate_content_sync(self, transcript: str) -> str:
        """Override in subclasses - synchronous version."""
        raise NotImplementedError
    
    def _get_fallback_content(self) -> str:
        """Fallback content when generation fails."""
        return f"# {self.name.title()}\n\nContent analysis for this section."

class TitleWorker(BaseWorker):
    """Generate SEO-optimized titles."""
    
    def __init__(self):
        super().__init__("title")
    
    def _generate_content_sync(self, transcript: str) -> str:
        messages = [
            {
                "role": "system",
                "content": "You are an expert content writer. Create an engaging, SEO-optimized title for this video content."
            },
            {
                "role": "user", 
                "content": f"Create a compelling title for this video content:\n\n{transcript[:2000]}"
            }
        ]
        
        result = self._call_openai_sync(messages, max_tokens=100)
        
        # Ensure it starts with #
        if not result.startswith('#'):
            result = f"# {result}"
        
        return result
    
    def _get_fallback_content(self) -> str:
        return "# Video Content Analysis\n\nComprehensive insights and key takeaways from this video."

class IntroWorker(BaseWorker):
    """Generate engaging introductions."""
    
    def __init__(self):
        super().__init__("intro")
    
    def _generate_content_sync(self, transcript: str) -> str:
        messages = [
            {
                "role": "system",
                "content": "Write an engaging introduction paragraph that hooks readers and summarizes what they'll learn."
            },
            {
                "role": "user",
                "content": f"Write an introduction for this video content:\n\n{transcript[:2000]}"
            }
        ]
        
        return self._call_openai_sync(messages, max_tokens=300)
    
    def _get_fallback_content(self) -> str:
        return "This video provides valuable insights and information on important topics that can benefit viewers interested in learning more about the subject matter."

class KeyPointsWorker(BaseWorker):
    """Extract key points and insights."""
    
    def __init__(self):
        super().__init__("key_points")
    
    def _generate_content_sync(self, transcript: str) -> str:
        messages = [
            {
                "role": "system",
                "content": "Extract the main key points and insights from this content. Format as a bulleted list with clear, actionable points."
            },
            {
                "role": "user",
                "content": f"Extract key points from:\n\n{transcript[:3000]}"
            }
        ]
        
        result = self._call_openai_sync(messages, max_tokens=800)
        
        # Ensure proper formatting
        if not result.startswith("##"):
            result = f"## Key Points\n\n{result}"
        
        return result
    
    def _get_fallback_content(self) -> str:
        return """## Key Points

• Important concepts and strategies discussed
• Practical insights for implementation  
• Notable observations and recommendations
• Valuable takeaways for viewers"""

class QuotesWorker(BaseWorker):
    """Extract notable quotes."""
    
    def __init__(self):
        super().__init__("quotes")
    
    def _generate_content_sync(self, transcript: str) -> str:
        messages = [
            {
                "role": "system",
                "content": "Extract 2-3 of the most impactful quotes from this content. Format each with quotation marks and context."
            },
            {
                "role": "user",
                "content": f"Find notable quotes from:\n\n{transcript[:3000]}"
            }
        ]
        
        result = self._call_openai_sync(messages, max_tokens=500)
        
        if not result.startswith("##"):
            result = f"## Notable Quotes\n\n{result}"
        
        return result
    
    def _get_fallback_content(self) -> str:
        return """## Notable Quotes

Key statements and insights that highlight important themes and provide valuable perspectives on the topic."""

class SummaryWorker(BaseWorker):
    """Generate comprehensive summaries."""
    
    def __init__(self):
        super().__init__("summary")
    
    def _generate_content_sync(self, transcript: str) -> str:
        messages = [
            {
                "role": "system",
                "content": "Create a concise but comprehensive summary that captures all the main points and takeaways."
            },
            {
                "role": "user",
                "content": f"Summarize this content:\n\n{transcript[:4000]}"
            }
        ]
        
        result = self._call_openai_sync(messages, max_tokens=600)
        
        if not result.startswith("##"):
            result = f"## Summary\n\n{result}"
        
        return result
    
    def _get_fallback_content(self) -> str:
        return """## Summary

This content provides valuable insights and practical information that can help viewers understand important concepts and apply them effectively."""

class ConclusionWorker(BaseWorker):
    """Generate compelling conclusions."""
    
    def __init__(self):
        super().__init__("conclusion")
    
    def _generate_content_sync(self, transcript: str) -> str:
        messages = [
            {
                "role": "system",
                "content": "Write a compelling conclusion that reinforces key takeaways and provides a call to action."
            },
            {
                "role": "user",
                "content": f"Write a conclusion for:\n\n{transcript[:2000]}"
            }
        ]
        
        result = self._call_openai_sync(messages, max_tokens=400)
        
        if not result.startswith("##"):
            result = f"## Conclusion\n\n{result}"
        
        return result
    
    def _get_fallback_content(self) -> str:
        return """## Conclusion

The insights and information shared provide valuable knowledge that can be applied to achieve better outcomes and continued growth in understanding."""

class SEOWorker(BaseWorker):
    """Generate SEO metadata."""
    
    def __init__(self):
        super().__init__("seo")
    
    def _generate_content_sync(self, transcript: str) -> str:
        messages = [
            {
                "role": "system",
                "content": "Generate SEO metadata: a meta description (150-160 chars) and keywords list."
            },
            {
                "role": "user",
                "content": f"Create SEO metadata for:\n\n{transcript[:1500]}"
            }
        ]
        
        result = self._call_openai_sync(messages, max_tokens=200)
        
        # Format as metadata
        if "META_DESCRIPTION:" not in result:
            lines = result.split('\n')
            formatted = f"META_DESCRIPTION: \"{lines[0][:160]}\"\nKEYWORDS: \"{', '.join(lines[1:3]) if len(lines) > 1 else 'content, analysis, insights'}\""
            result = formatted
        
        return result
    
    def _get_fallback_content(self) -> str:
        return 'META_DESCRIPTION: "Comprehensive analysis and insights from video content"\nKEYWORDS: "analysis, insights, video content, information"'

class TagsWorker(BaseWorker):
    """Generate relevant tags."""
    
    def __init__(self):
        super().__init__("tags")
    
    def _generate_content_sync(self, transcript: str) -> str:
        messages = [
            {
                "role": "system",
                "content": "Generate 5-8 relevant hashtags for this content."
            },
            {
                "role": "user",
                "content": f"Generate hashtags for:\n\n{transcript[:1000]}"
            }
        ]
        
        result = self._call_openai_sync(messages, max_tokens=100)
        
        # Ensure proper formatting
        if not result.startswith("Tags:") and not result.startswith("#"):
            result = f"Tags: {result}"
        
        return result
    
    def _get_fallback_content(self) -> str:
        return "Tags: #analysis #insights #content #information #video"
