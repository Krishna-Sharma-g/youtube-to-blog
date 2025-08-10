from __future__ import annotations
import requests
import json
import os
import streamlit as st
import time
from typing import List, Dict

def chunk_text(text: str, max_words: int = 800) -> List[str]:
    """Split text into manageable chunks for detailed analysis."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = ' '.join(words[i:i + max_words])
        if chunk.strip():
            chunks.append(chunk)
    return chunks

class BaseWorker:
    """Enhanced base worker for premium content generation."""
    
    def __init__(self, name: str):
        self.name = name
    
    def get_openai_api_key(self):
        """Get OpenAI API key with proper error handling."""
        try:
            api_key = st.secrets["OPENAI_API_KEY"]
            if api_key and api_key.startswith("sk-"):
                return api_key
        except:
            pass
        
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key.startswith("sk-"):
            return api_key
        
        raise ValueError("OpenAI API key not found or invalid")
    
    def _call_openai_premium(self, messages: List[Dict], max_tokens: int = 2000) -> str:
        """Premium OpenAI call with enhanced parameters."""
        try:
            api_key = self.get_openai_api_key()
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-4o",  # Use GPT-4 for better quality
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.8,  # Higher creativity
                "presence_penalty": 0.1,
                "frequency_penalty": 0.1
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=120  # Longer timeout for detailed content
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return content.strip()
            else:
                raise Exception(f"OpenAI API Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"[{self.name}] Premium OpenAI call failed: {e}")
            raise e
    
    async def generate(self, transcript: str) -> str:
        """Generate premium content with chunking and detailed analysis."""
        try:
            if not transcript or len(transcript) < 100:
                return self._get_fallback_content()
            
            # Chunk transcript for detailed analysis
            chunks = chunk_text(transcript, max_words=1000)
            
            import asyncio
            return await asyncio.to_thread(self._generate_premium_content, chunks)
            
        except Exception as e:
            print(f"[{self.name}] Generation failed: {e}")
            return self._get_fallback_content()
    
    def _generate_premium_content(self, chunks: List[str]) -> str:
        """Override in subclasses for premium content generation."""
        raise NotImplementedError
    
    def _get_fallback_content(self) -> str:
        """High-quality fallback content."""
        return f"## {self.name.title()} Analysis\n\nDetailed analysis of this content section."

class TitleWorker(BaseWorker):
    """Generate compelling, SEO-optimized titles."""
    
    def __init__(self):
        super().__init__("title")
    
    def _generate_premium_content(self, chunks: List[str]) -> str:
        # Use first chunk for title generation
        primary_content = chunks[0] if chunks else ""
        
        messages = [
            {
                "role": "system",
                "content": """You are an expert content writer and SEO specialist. Create compelling, click-worthy titles that:
                - Are emotionally engaging and curiosity-driven
                - Include specific benefits or outcomes
                - Use power words and numbers when appropriate
                - Are optimized for search engines
                - Capture the essence of the content perfectly
                
                Examples of great titles:
                - "How I Landed My Dream Internship at IIT Bombay: A Complete Interview Journey"
                - "From 4000 Applicants to Final Selection: My Trust Lab Experience"
                - "The 10 Life-Changing Rules That Transformed My 2025 (Backed by Science)"
                """
            },
            {
                "role": "user",
                "content": f"""Create a compelling, detailed title for this video content. Make it engaging and specific:

{primary_content[:1500]}

Generate ONLY the title with a # markdown header. Make it feel personal and story-driven."""
            }
        ]
        
        result = self._call_openai_premium(messages, max_tokens=200)
        
        if not result.startswith('#'):
            result = f"# {result}"
        
        return result
    
    def _get_fallback_content(self) -> str:
        return "# Insights and Lessons from This Video: A Deep Dive Analysis"

class IntroWorker(BaseWorker):
    """Generate engaging, story-driven introductions."""
    
    def __init__(self):
        super().__init__("intro")
    
    def _generate_premium_content(self, chunks: List[str]) -> str:
        # Use first 2 chunks for comprehensive intro
        intro_content = ' '.join(chunks[:2]) if len(chunks) >= 2 else chunks[0] if chunks else ""
        
        messages = [
            {
                "role": "system",
                "content": """You are a master storyteller and content writer. Create engaging introductions that:
                - Hook the reader immediately with a compelling opening
                - Set the scene and provide context
                - Create emotional connection
                - Promise valuable insights
                - Use narrative techniques and personal language
                - Are 200-400 words long
                
                Study this example style:
                "I hope you've read the article I published recently. If it isn't the case, you can read it to get a broader understanding. I'll come straight to the point of article, considering the case that you're familiar about internships at esteemed research institutes."
                
                Write in first person when appropriate, create suspense, and make it feel like a personal story."""
            },
            {
                "role": "user",
                "content": f"""Write a compelling, engaging introduction for this video content. Make it feel like a personal story that draws readers in:

{intro_content[:2000]}

Create a narrative introduction that hooks the reader and sets up the content beautifully. Use storytelling techniques and make it personal."""
            }
        ]
        
        return self._call_openai_premium(messages, max_tokens=600)
    
    def _get_fallback_content(self) -> str:
        return """Have you ever wondered what separates successful people from the rest? In this comprehensive analysis, we dive deep into strategies and insights that can transform your approach to life and work. 

What you're about to discover isn't just another collection of tips – it's a detailed breakdown of proven principles that have helped countless individuals achieve their goals and create meaningful change in their lives."""

class KeyPointsWorker(BaseWorker):
    """Extract and elaborate on key insights with detailed analysis."""
    
    def __init__(self):
        super().__init__("key_points")
    
    def _generate_premium_content(self, chunks: List[str]) -> str:
        # Use all chunks for comprehensive key points analysis
        full_content = ' '.join(chunks)
        
        messages = [
            {
                "role": "system",
                "content": """You are an expert analyst and content strategist. Extract and elaborate on key points with:
                - Detailed explanations of each concept
                - Practical applications and examples
                - Why each point matters
                - How to implement the insights
                - Personal reflections where appropriate
                - Rich, narrative descriptions
                
                Format as clear sections with headers and detailed explanations. Make each point substantial and valuable.
                
                Example format:
                ## Key Insights and Strategies
                
                ### 1. The Power of Strategic Thinking
                [Detailed explanation with examples and applications]
                
                ### 2. Building Resilience in Challenging Times
                [In-depth analysis with actionable steps]
                """
            },
            {
                "role": "user",
                "content": f"""Analyze this content and extract the most important insights. Provide detailed explanations, practical applications, and rich context for each key point:

{full_content[:4000]}

Create comprehensive, detailed key points that provide real value to readers. Make each point substantial with explanations and examples."""
            }
        ]
        
        return self._call_openai_premium(messages, max_tokens=2000)
    
    def _get_fallback_content(self) -> str:
        return """## Key Insights and Strategies

### 1. Strategic Mindset Development
Understanding how to think strategically about your goals and approach challenges with a systematic mindset.

### 2. Building Sustainable Habits
Creating systems and routines that support long-term growth and success.

### 3. Leveraging Opportunities
Recognizing and capitalizing on moments that can accelerate your progress."""

class QuotesWorker(BaseWorker):
    """Extract meaningful quotes with rich context and analysis."""
    
    def __init__(self):
        super().__init__("quotes")
    
    def _generate_premium_content(self, chunks: List[str]) -> str:
        # Use all chunks to find the best quotes
        full_content = ' '.join(chunks)
        
        messages = [
            {
                "role": "system",
                "content": """You are a content curator specializing in extracting meaningful quotes. Find the most impactful statements and:
                - Provide rich context for each quote
                - Explain why it's significant
                - Connect it to broader themes
                - Add analytical commentary
                - Show practical applications
                
                Format example:
                ## Notable Insights and Quotes
                
                > "Success is not just about luck but also about mindset, dedication, and hard work."
                
                This powerful statement encapsulates the multi-faceted nature of achievement. It challenges the common misconception that success is purely circumstantial, instead highlighting the critical role of personal agency and consistent effort. The emphasis on mindset particularly resonates because...
                """
            },
            {
                "role": "user",
                "content": f"""Extract the most meaningful and impactful quotes from this content. Provide rich context, analysis, and significance for each quote:

{full_content[:4000]}

Find 3-4 powerful quotes and provide detailed context and analysis for each. Make them meaningful and well-explained."""
            }
        ]
        
        return self._call_openai_premium(messages, max_tokens=1200)
    
    def _get_fallback_content(self) -> str:
        return """## Notable Insights and Quotes

> "Success requires both strategic thinking and consistent execution."

This insight highlights the dual nature of achievement - having a clear plan while maintaining the discipline to follow through consistently.

> "The difference between successful and unsuccessful people often lies in how they handle setbacks."

A powerful reminder that resilience and adaptability are crucial skills for long-term success."""

class SummaryWorker(BaseWorker):
    """Generate comprehensive, insightful summaries."""
    
    def __init__(self):
        super().__init__("summary")
    
    def _generate_premium_content(self, chunks: List[str]) -> str:
        # Use all chunks for comprehensive summary
        full_content = ' '.join(chunks)
        
        messages = [
            {
                "role": "system",
                "content": """You are an expert content synthesizer. Create comprehensive summaries that:
                - Capture all major themes and insights
                - Provide analytical depth
                - Connect different concepts together
                - Offer broader context and implications
                - Are well-structured and narrative-driven
                - Feel like a thoughtful analysis, not just bullet points
                
                Write in a flowing, analytical style that demonstrates deep understanding of the content."""
            },
            {
                "role": "user",
                "content": f"""Create a comprehensive, analytical summary of this content. Synthesize the main themes, insights, and implications:

{full_content[:4000]}

Write a detailed summary that demonstrates deep understanding and provides valuable analysis. Make it substantial and insightful."""
            }
        ]
        
        result = self._call_openai_premium(messages, max_tokens=1000)
        
        if not result.startswith("##"):
            result = f"## Summary and Analysis\n\n{result}"
        
        return result
    
    def _get_fallback_content(self) -> str:
        return """## Summary and Analysis

This content provides a comprehensive exploration of strategies and principles that can drive meaningful change and success. The analysis reveals several interconnected themes around mindset development, strategic thinking, and practical implementation of growth-oriented behaviors."""

class ConclusionWorker(BaseWorker):
    """Generate compelling, actionable conclusions."""
    
    def __init__(self):
        super().__init__("conclusion")
    
    def _generate_premium_content(self, chunks: List[str]) -> str:
        # Use last chunks and overall theme for conclusion
        conclusion_content = ' '.join(chunks[-2:]) if len(chunks) >= 2 else chunks[-1] if chunks else ""
        
        messages = [
            {
                "role": "system",
                "content": """You are a motivational writer and strategist. Create powerful conclusions that:
                - Reinforce key takeaways
                - Provide clear next steps
                - Inspire action
                - Connect to the reader's journey
                - Feel personal and motivating
                - Include specific calls to action
                
                Study this style:
                "Let this video be a catalyst for positive change in your life. Embrace the mindset of a winner, set your goals high, and take proactive steps towards achieving your dreams. Remember, success is within your reach if you are willing to put in the work. Start today and pave the way for a brighter future."
                
                Make it inspirational but practical."""
            },
            {
                "role": "user",
                "content": f"""Write a compelling conclusion that inspires action and provides clear next steps based on this content:

{conclusion_content[:2000]}

Create a motivational yet practical conclusion that helps readers take action. Make it personal and actionable."""
            }
        ]
        
        result = self._call_openai_premium(messages, max_tokens=600)
        
        if not result.startswith("##"):
            result = f"## Moving Forward: Your Next Steps\n\n{result}"
        
        return result
    
    def _get_fallback_content(self) -> str:
        return """## Moving Forward: Your Next Steps

The insights and strategies covered here provide a solid foundation for meaningful change and growth. The key to success lies not just in understanding these concepts, but in consistently applying them to your daily life and long-term goals.

Start by choosing one or two key principles that resonate most with your current situation. Focus on implementing these gradually, building sustainable habits that will compound over time. Remember, transformation is a journey that requires both patience and persistence.

Take action today – even small steps forward are better than standing still."""

class SEOWorker(BaseWorker):
    """Generate comprehensive SEO metadata."""
    
    def __init__(self):
        super().__init__("seo")
    
    def _generate_premium_content(self, chunks: List[str]) -> str:
        # Use full content for SEO analysis
        full_content = ' '.join(chunks)
        
        messages = [
            {
                "role": "system",
                "content": """You are an SEO expert. Generate comprehensive metadata including:
                - Compelling meta description (150-160 characters)
                - Relevant keywords (focus + long-tail)
                - Topic clusters
                
                Format as:
                META_DESCRIPTION: "[Engaging description that includes key benefit/outcome]"
                KEYWORDS: "[Primary keyword], [secondary keywords], [long-tail keywords]"
                """
            },
            {
                "role": "user",
                "content": f"""Generate SEO metadata for this content:

{full_content[:2000]}

Create compelling meta description and relevant keywords."""
            }
        ]
        
        return self._call_openai_premium(messages, max_tokens=300)
    
    def _get_fallback_content(self) -> str:
        return 'META_DESCRIPTION: "Discover proven strategies and insights for personal growth and success. Learn actionable techniques that can transform your mindset and accelerate your progress."\nKEYWORDS: "personal development, success strategies, mindset transformation, growth mindset, life improvement, productivity tips"'

class TagsWorker(BaseWorker):
    """Generate relevant, strategic tags."""
    
    def __init__(self):
        super().__init__("tags")
    
    def _generate_premium_content(self, chunks: List[str]) -> str:
        # Use content overview for tag generation
        content_sample = ' '.join(chunks)[:1500]
        
        messages = [
            {
                "role": "system",
                "content": """Generate 8-12 strategic hashtags that:
                - Mix popular and niche tags
                - Include topic-specific keywords
                - Cover different aspects of the content
                - Are actually searchable and relevant
                
                Format: Tags: #tag1 #tag2 #tag3 etc."""
            },
            {
                "role": "user",
                "content": f"""Generate strategic hashtags for this content:

{content_sample}

Create relevant, searchable tags that cover the main topics."""
            }
        ]
        
        return self._call_openai_premium(messages, max_tokens=150)
    
    def _get_fallback_content(self) -> str:
        return "Tags: #PersonalDevelopment #SuccessStrategies #MindsetGrowth #SelfImprovement #ProductivityTips #LifeHacks #Motivation #GoalSetting #PersonalGrowth #Leadership"
