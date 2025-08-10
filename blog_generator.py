#!/usr/bin/env python3
"""
YouTube Blog Generator - CLI Interface

Usage:
    python blog_generator.py "https://www.youtube.com/watch?v=VIDEO_ID"
    python blog_generator.py "https://www.youtube.com/watch?v=VIDEO_ID" --output custom_blog.md
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).resolve().parent / "src"))

from orchestrator import BlogOrchestrator

async def main():
    parser = argparse.ArgumentParser(
        description="Generate blog posts from YouTube videos"
    )
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "--output", "-o", 
        default="blog_post.md",
        help="Output file path (default: blog_post.md)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true", 
        help="Show detailed progress"
    )
    
    args = parser.parse_args()
    
    orchestrator = BlogOrchestrator()
    
    try:
        print(f"🎬 Processing: {args.url}")
        
        blog_data = await orchestrator.generate_blog_post(args.url)
        
        output_path = Path(args.output)
        await orchestrator.save_blog_post(blog_data, output_path)
        
        print(f"✅ Blog post generated successfully!")
        print(f"📄 Output: {output_path.absolute()}")
        print(f"📊 Word count: ~{len(blog_data['content'].split())}")
        
        if args.verbose:
            print("\n--- PREVIEW ---")
            print(blog_data["content"][:500] + "..." if len(blog_data["content"]) > 500 else blog_data["content"])
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
