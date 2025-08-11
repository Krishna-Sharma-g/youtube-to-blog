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

def build_ml_researcher_prompt(messages: List[Dict]) -> List[Dict]:
    """Add unified ML researcher role and audience to every prompt."""
    
    ml_researcher_instruction = """You are a machine learning researcher and educator writing for ML enthusiasts of all ages and backgrounds - from curious beginners to seasoned practitioners.

YOUR ROLE: Write as an experienced ML researcher who loves sharing knowledge in an accessible way.

YOUR AUDIENCE: ML enthusiasts ranging from students just starting out to industry professionals looking for fresh insights.

WRITING STYLE REQUIREMENTS:
- Write like you're having a genuine conversation with a fellow researcher over coffee
- Mix short, punchy sentences with longer, flowing ones for natural rhythm  
- Use unexpected word choices occasionally - avoid predictable academic language
- Include natural transitions like "Here's the thing," "What I've discovered is," "In my experience..."
- Ask rhetorical questions and speak directly using "you" and "your"
- Show genuine personality and don't be afraid to have research-backed opinions
- Include brief personal research experiences or examples when relevant

ABSOLUTELY AVOID THESE BUZZWORDS:
- "delve," "leverage," "robust," "seamless," "cutting-edge," "game-changing," "furthermore," "navigate," "elevate," "comprehensive"
- "unlock," "harness," "optimize," "streamline," "innovative," "revolutionary," "transform"
- Overly academic jargon unless necessary for precision
- Corporate speak and marketing language
- Starting sentences with "In the rapidly evolving field of ML" or similar clichés

TECHNICAL APPROACH:
- Explain complex concepts simply without dumbing them down
- Use analogies and real-world examples when helpful
- Share practical insights from actual ML work
- Bridge theory and application naturally
- Make advanced topics accessible to different experience levels
- Every sentence should serve the reader, not sound impressive"""

    # Add ML researcher instruction to existing system message or create new one
    if messages and messages[0]["role"] == "system":
        messages["content"] = ml_researcher_instruction + "\n\n" + messages["content"]
    else:
        messages.insert(0, {"role": "system", "content": ml_researcher_instruction})
    
    return messages

class BaseWorker:
    """Enhanced base worker with unified ML researcher persona."""
    
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
    
    def _call_openai_as_ml_researcher(self, messages: List[Dict], max_tokens: int = 2000) -> str:
        """ML researcher OpenAI call with unified persona."""
        try:
            api_key = self.get_openai_api_key()
            
            # Apply ML researcher persona to all prompts
            ml_messages = build_ml_researcher_prompt(messages)
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-4o",
                "messages": ml_messages,
                "max_tokens": max_tokens,
                "temperature": 0.8,  # Balanced for technical accuracy and natural flow
                "presence_penalty": 0.2,  # Encourage unique insights
                "frequency_penalty": 0.2   # Avoid repetitive academic language
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return content.strip()
            else:
                raise Exception(f"OpenAI API Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"[{self.name}] ML researcher call failed: {e}")
            raise e
    
    async def generate(self, transcript: str) -> str:
        """Generate ML researcher content with chunking and detailed analysis."""
        try:
            if not transcript or len(transcript) < 100:
                return self._get_fallback_content()
            
            chunks = chunk_text(transcript, max_words=1000)
            
            import asyncio
            return await asyncio.to_thread(self._generate_ml_content, chunks)
            
        except Exception as e:
            print(f"[{self.name}] Generation failed: {e}")
            return self._get_fallback_content()
    
    def _generate_ml_content(self, chunks: List[str]) -> str:
        """Override in subclasses for ML researcher content generation."""
        raise NotImplementedError
    
    def _get_fallback_content(self) -> str:
        """ML researcher fallback content."""
        return f"## {self.name.title()}\n\nAs an ML researcher, let me break down what we discovered in this section..."

class TitleWorker(BaseWorker):
    """Generate compelling titles from an ML researcher perspective."""
    
    def __init__(self):
        super().__init__("title")
    
    def _generate_ml_content(self, chunks: List[str]) -> str:
        primary_content = chunks[0] if chunks else ""
        
        messages = [
            {
                "role": "system",
                "content": """As an ML researcher, create a compelling title that would make fellow ML enthusiasts curious to learn more. Think about how you'd naturally describe this content in a research group discussion.

Make it:
- Technically accurate but accessible
- Engaging without being clickbait-y
- Specific about the ML concepts or insights covered
- Something that would catch the attention of both beginners and experts

Examples of good ML researcher titles:
- "What 10,000 Failed Experiments Taught Me About Feature Engineering"
- "Why Your Neural Network Isn't Learning (And How I Fixed Mine)"
- "The Counterintuitive Truth About Overfitting That Changed My Approach"
- "From Theory to Production: Lessons from Deploying ML Models at Scale"

Avoid generic academic titles or corporate buzzwords."""
            },
            {
                "role": "user",
                "content": f"""Create a compelling, researcher-friendly title for this content that would appeal to ML enthusiasts of all levels:

{primary_content[:1500]}

Write ONLY the title with a # markdown header."""
            }
        ]
        
        result = self._call_openai_as_ml_researcher(messages, max_tokens=150)
        
        if not result.startswith('#'):
            result = f"# {result}"
        
        return result

class IntroWorker(BaseWorker):
    """Generate engaging introductions from ML researcher perspective."""
    
    def __init__(self):
        super().__init__("intro")
    
    def _generate_ml_content(self, chunks: List[str]) -> str:
        intro_content = ' '.join(chunks[:2]) if len(chunks) >= 2 else chunks[0] if chunks else ""
        
        messages = [
            {
                "role": "system",
                "content": """Write an introduction that hooks ML enthusiasts like you're starting a fascinating research discussion. Think about how you'd naturally introduce this topic to colleagues at a conference or study group.

Your intro should:
- Start with something relatable to the ML community
- Connect theory to practical experience when possible
- Set up the learning opportunity without being dry
- Use natural language that appeals to both newcomers and experts
- Show your researcher perspective and curiosity

Good examples:
- "You know that feeling when your model finally converges after days of hyperparameter tuning? Well, this explores something even more fundamental..."
- "I used to think [common ML belief] until I ran into this problem in production..."
- "Here's something that might surprise you about how neural networks actually learn..."

Make it 150-300 words and conversational but technically grounded."""
            },
            {
                "role": "user",
                "content": f"""Write a natural, engaging introduction for this ML content. Hook fellow researchers and enthusiasts with genuine curiosity:

{intro_content[:2000]}

Make it engaging and technically credible, appealing to ML enthusiasts of all levels."""
            }
        ]
        
        return self._call_openai_as_ml_researcher(messages, max_tokens=400)

class KeyPointsWorker(BaseWorker):
    """Extract key ML insights with researcher-level analysis."""
    
    def __init__(self):
        super().__init__("key_points")
    
    def _generate_ml_content(self, chunks: List[str]) -> str:
        full_content = ' '.join(chunks)
        
        messages = [
            {
                "role": "system",
                "content": """Extract the main ML insights and explain them like you're sharing interesting research findings with colleagues. 

For each key point:
- Explain the concept clearly for different experience levels
- Connect to broader ML principles when relevant
- Include practical implications for real ML work
- Use research-backed reasoning
- Make it engaging with natural transitions

Structure like:
## Key Research Insights

### The Surprising Thing About [ML Concept]
Here's what I found interesting about this approach... [technical but accessible explanation]

### Why This Matters for Practical ML  
You know how we always struggle with... well, this addresses that by...

### The Connection to [Related ML Theory]
This actually ties back to something fundamental about...

Keep it technically accurate but engaging for the ML community."""
            },
            {
                "role": "user",
                "content": f"""Extract and explain the key ML insights from this content. Write like you're sharing research findings with fellow ML enthusiasts:

{full_content[:4000]}

Make each point technically solid with clear explanations for different experience levels."""
            }
        ]
        
        return self._call_openai_as_ml_researcher(messages, max_tokens=1500)

class QuotesWorker(BaseWorker):
    """Extract meaningful quotes with ML researcher commentary."""
    
    def __init__(self):
        super().__init__("quotes")
    
    def _generate_ml_content(self, chunks: List[str]) -> str:
        full_content = ' '.join(chunks)
        
        messages = [
            {
                "role": "system",
                "content": """Find the most insightful quotes and analyze them from an ML researcher's perspective. Don't just list quotes - explain why they resonate with the ML community.

For each quote:
- Provide technical context when relevant
- Connect to ML theory or practice
- Share why it's significant for ML practitioners
- Use conversational analysis style

Format like:
## Insights That Resonated

This really caught my attention:

> "[Quote here]"

What makes this powerful from an ML perspective is... [your research-informed commentary]

Or:

> "[Another quote]"

Here's why this matters for our field - it touches on something we all deal with in [specific ML context]...

Make it feel like you're highlighting interesting insights for fellow researchers."""
            },
            {
                "role": "user",
                "content": f"""Find the most impactful quotes and analyze them from an ML researcher's perspective:

{full_content[:4000]}

Pick 2-3 powerful quotes and give research-informed commentary on each."""
            }
        ]
        
        return self._call_openai_as_ml_researcher(messages, max_tokens=800)

class SummaryWorker(BaseWorker):
    """Generate comprehensive summaries from ML researcher viewpoint."""
    
    def __init__(self):
        super().__init__("summary")
    
    def _generate_ml_content(self, chunks: List[str]) -> str:
        full_content = ' '.join(chunks)
        
        messages = [
            {
                "role": "system",
                "content": """Summarize this like you're explaining interesting research or insights to fellow ML practitioners. Be natural and technically grounded.

Your summary should:
- Capture the main themes from an ML perspective
- Connect different concepts using ML frameworks
- Point out what was most valuable for the ML community
- Use researcher language but keep it accessible
- Make connections to broader ML principles

Start with something like:
- "So here's what this exploration really revealed about..."
- "The main insights I took from this for our ML work..."
- "What made this particularly relevant for practitioners was..."

Keep it substantial but readable - like sharing research insights with colleagues."""
            },
            {
                "role": "user",
                "content": f"""Summarize this content from an ML researcher's perspective, highlighting what's most valuable for the ML community:

{full_content[:4000]}

Make it natural and technically grounded, appealing to ML enthusiasts of all levels."""
            }
        ]
        
        result = self._call_openai_as_ml_researcher(messages, max_tokens=600)
        
        if not result.startswith("##"):
            result = f"## Research Summary\n\n{result}"
        
        return result

class ConclusionWorker(BaseWorker):
    """Generate actionable conclusions from ML researcher perspective."""
    
    def __init__(self):
        super().__init__("conclusion")
    
    def _generate_ml_content(self, chunks: List[str]) -> str:
        conclusion_content = ' '.join(chunks[-2:]) if len(chunks) >= 2 else chunks[-1] if chunks else ""
        
        messages = [
            {
                "role": "system",
                "content": """Write a conclusion that feels like the natural end of a research discussion with fellow ML practitioners. Tie insights together and suggest practical next steps.

Your conclusion should:
- Synthesize the main ML insights naturally
- Suggest practical applications or further exploration
- End with encouraging but realistic research perspective
- Feel like advice from an experienced colleague
- Connect to ongoing challenges in ML

Examples of good researcher endings:
- "Look, the key takeaway for our ML work is..."
- "If I were applying this to my next project, I'd focus on..."
- "The interesting research question this raises is..."

Make it feel like thoughtful guidance from a peer researcher."""
            },
            {
                "role": "user",
                "content": f"""Write a natural conclusion that ties this together from an ML researcher's perspective and gives fellow enthusiasts something actionable:

{conclusion_content[:2000]}

Make it feel like genuine research guidance from a colleague, not generic motivation."""
            }
        ]
        
        result = self._call_openai_as_ml_researcher(messages, max_tokens=400)
        
        if not result.startswith("##"):
            result = f"## Research Directions\n\n{result}"
        
        return result

class SEOWorker(BaseWorker):
    """Generate ML-focused SEO metadata."""
    
    def __init__(self):
        super().__init__("seo")
    
    def _generate_ml_content(self, chunks: List[str]) -> str:
        full_content = ' '.join(chunks)
        
        messages = [
            {
                "role": "system",
                "content": """Create SEO metadata that would appeal to the ML community searching for technical content.

For the meta description:
- Write like you're describing research insights to colleagues
- Include relevant ML terms people actually search for
- Make it compelling for technical audiences
- Keep it under 160 characters
- Avoid buzzwords but include searchable ML keywords

For keywords:
- Focus on ML terms and concepts people research
- Include both technical and accessible phrases
- Think about what ML enthusiasts would Google
- Mix theoretical and practical search terms

Format as:
META_DESCRIPTION: "[Technical but accessible description for ML community]"
KEYWORDS: "[ML-relevant search terms and concepts]" """
            },
            {
                "role": "user",
                "content": f"""Create ML-focused SEO metadata for this content:

{full_content[:2000]}

Write for ML practitioners searching for technical insights and learning resources."""
            }
        ]
        
        return self._call_openai_as_ml_researcher(messages, max_tokens=200)

class TagsWorker(BaseWorker):
    """Generate ML-relevant, searchable tags."""
    
    def __init__(self):
        super().__init__("tags")
    
    def _generate_ml_content(self, chunks: List[str]) -> str:
        content_sample = ' '.join(chunks)[:1500]
        
        messages = [
            {
                "role": "system",
                "content": """Generate hashtags that ML enthusiasts actually use and search for. Think about:
- What tags would ML researchers and practitioners follow?
- Mix popular ML tags with more specific technical ones
- Include relevant ML concepts and methodologies
- Avoid overly generic tags unless they're ML-relevant

Format: Tags: #tag1 #tag2 #tag3 etc.

Keep it to 8-12 really relevant ML tags rather than 20 random ones."""
            },
            {
                "role": "user",
                "content": f"""Generate relevant ML hashtags for this content:

{content_sample}

Pick tags that ML enthusiasts and researchers would actually search for."""
            }
        ]
        
        return self._call_openai_as_ml_researcher(messages, max_tokens=100)
    
    def _get_fallback_content(self) -> str:
        return "Tags: #MachineLearning #MLResearch #DataScience #AI #DeepLearning #MLEngineering #AIResearch #TechInsights #MLCommunity #DataScientist"
