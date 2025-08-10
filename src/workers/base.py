from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any
from utils.openai_client import chat

class BlogWorker(ABC):
    """
    Abstract base class for all blog section generators.
    Each worker produces one section of the final blog post.
    """
    
    def __init__(self, name: str, max_tokens: int = 300):
        self.name = name
        self.max_tokens = max_tokens
    
    @abstractmethod
    def get_prompt(self, transcript: str, context: Dict[str, Any] = None) -> str:
        """Return the specific prompt for this worker's task."""
        pass
    
    @abstractmethod  
    def format_output(self, raw_output: str) -> str:
        """Format the LLM output into proper Markdown for this section."""
        pass
    
    async def generate(self, transcript: str, context: Dict[str, Any] = None) -> str:
        """Generate this section's content."""
        prompt = self.get_prompt(transcript, context or {})
        
        response = await chat(
            [{"role": "user", "content": prompt}],
            max_tokens=self.max_tokens,
            temperature=0.7
        )
        
        return self.format_output(response)
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"
