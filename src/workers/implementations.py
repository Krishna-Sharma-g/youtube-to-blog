from __future__ import annotations
import requests
import json
import os
import streamlit as st
import time
from typing import List, Dict

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
                api_key = os.getenv("OPENAI_API_KEY")  # Now 'os' is imported!
            
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
    def __init__(self):
        super().__init__("title")
    
    def _generate_content_sync(self, transcript: str) -> str:
        messages = [
            {"role": "system", "content": "Create an engaging, SEO-optimized title for this video content."},
            {"role": "user", "content": f"Create a compelling title for:\n\n{transcript[:2000]}"}
        ]
        
        result = self._call_openai_sync(messages, max_tokens=100)
        if not result.startswith('#'):
            result = f"# {result}"
        return result
    
    def _get_fallback_content(self) -> str:
        return "# Video Content Analysis\n\nComprehensive insights and key takeaways from this video."

class IntroWorker(BaseWorker):
    def __init__(self):
        super().__init__("intro")
    
    def _generate_content_sync(self, transcript: str) -> str:
        messages = [
            {"role": "system", "content": "Write an engaging introduction paragraph."},
            {"role": "user", "content": f"Write an introduction for:\n\n{transcript[:2000]}"}
        ]
        return self._call_openai_sync(messages, max_tokens=300)
    
    def _get_fallback_content(self) -> str:
        return "This video provides valuable insights and information on important topics."

class KeyPointsWorker(BaseWorker):
    def __init__(self):
        super().__init__("key_points")
    
    def _generate_content_sync(self, transcript: str) -> str:
        messages = [
            {"role": "system", "content": "Extract main key points as a bulleted list."},
            {"role": "user", "content": f"Extract key points from:\n\n{transcript[:3000]}"}
        ]
        
        result = self._call_openai_sync(messages, max_tokens=800)
        if not result.startswith("##"):
            result = f"## Key Points\n\n{result}"
        return result
    
    def _get_fallback_content(self) -> str:
        return "## Key Points\n\n• Important concepts discussed\n• Practical insights for implementation\n• Notable recommendations"

class QuotesWorker(BaseWorker):
    def __init__(self):
        super().__init__("quotes")
    
    def _generate_content_sync(self, transcript: str) -> str:
        messages = [
            {"role": "system", "content": "Extract 2-3 impactful quotes with context."},
            {"role": "user", "content": f"Find notable quotes from:\n\n{transcript[:3000]}"}
        ]
        
        result = self._call_openai_sync(messages, max_tokens=500)
        if not result.startswith("##"):
            result = f"## Notable Quotes\n\n{result}"
        return result
    
    def _get_fallback_content(self) -> str:
        return "## Notable Quotes\n\nKey statements that highlight important themes and concepts."

class SummaryWorker(BaseWorker):
    def __init__(self):
        super().__init__("summary")
    
    def _generate_content_sync(self, transcript: str) -> str:
        messages = [
            {"role": "system", "content": "Create a comprehensive summary of main points."},
            {"role": "user", "content": f"Summarize:\n\n{transcript[:4000]}"}
        ]
        
        result = self._call_openai_sync(messages, max_tokens=600)
        if not result.startswith("##"):
            result = f"## Summary\n\n{result}"
        return result
    
    def _get_fallback_content(self) -> str:
        return "## Summary\n\nThis content provides valuable insights and practical information."

class ConclusionWorker(BaseWorker):
    def __init__(self):
        super().__init__("conclusion")
    
    def _generate_content_sync(self, transcript: str) -> str:
        messages = [
            {"role": "system", "content": "Write a compelling conclusion with call to action."},
            {"role": "user", "content": f"Write conclusion for:\n\n{transcript[:2000]}"}
        ]
        
        result = self._call_openai_sync(messages, max_tokens=400)
        if not result.startswith("##"):
            result = f"## Conclusion\n\n{result}"
        return result
    
    def _get_fallback_content(self) -> str:
        return "## Conclusion\n\nThe insights shared provide valuable knowledge for continued growth."

class SEOWorker(BaseWorker):
    def __init__(self):
        super().__init__("seo")
    
    def _generate_content_sync(self, transcript: str) -> str:
        messages = [
            {"role": "system", "content": "Generate meta description and keywords."},
            {"role": "user", "content": f"Create SEO metadata for:\n\n{transcript[:1500]}"}
        ]
        
        result = self._call_openai_sync(messages, max_tokens=200)
        if "META_DESCRIPTION:" not in result:
            result = f'META_DESCRIPTION: "{result[:160]}"\nKEYWORDS: "content, analysis, insights"'
        return result
    
    def _get_fallback_content(self) -> str:
        return 'META_DESCRIPTION: "Video content analysis and insights"\nKEYWORDS: "analysis, insights, video, content"'

class TagsWorker(BaseWorker):
    def __init__(self):
        super().__init__("tags")
    
    def _generate_content_sync(self, transcript: str) -> str:
        messages = [
            {"role": "system", "content": "Generate 5-8 relevant hashtags."},
            {"role": "user", "content": f"Generate hashtags for:\n\n{transcript[:1000]}"}
        ]
        
        result = self._call_openai_sync(messages, max_tokens=100)
        if not result.startswith("Tags:") and not result.startswith("#"):
            result = f"Tags: {result}"
        return result
    
    def _get_fallback_content(self) -> str:
        return "Tags: #analysis #insights #content #information #video"
