#!/usr/bin/env python3
"""
YouTube Blog Generator - FINAL BULLETPROOF VERSION
No more placeholder content - only real blogs or clear error messages!
"""

import streamlit as st
import asyncio
import sys
from pathlib import Path
import time
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parent / "src"))

from orchestrator import BlogOrchestrator

st.set_page_config(
    page_title="YouTube to Blog Generator",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS (keeping existing styles)
st.markdown("""
<style>
    .main-header { text-align: center; color: #FF6B6B; font-size: 3rem; margin-bottom: 0.5rem; }
    .sub-header { text-align: center; color: #666; font-size: 1.2rem; margin-bottom: 2rem; }
    .success-box { background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0; }
    .error-box { background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0; }
    .warning-box { background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0; }
    .blog-container { background-color: #f8f9fa; padding: 2rem; border-radius: 1rem; border-left: 5px solid #FF6B6B; margin: 1rem 0; }
    .stats-box { background-color: #e3f2fd; border: 1px solid #90caf9; color: #0d47a1; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">🎬 → 📝</h1>', unsafe_allow_html=True)
    st.markdown('<h2 class="main-header">YouTube to Blog Generator</h2>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Transform YouTube videos into comprehensive blog posts - NO PLACEHOLDER CONTENT!</p>', unsafe_allow_html=True)
    
    # Input section
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        youtube_url = st.text_input(
            "📎 Enter YouTube URL:",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Paste any PUBLIC YouTube video URL with clear speech",
            key="url_input"
        )
        
        generate_clicked = st.button(
            "🚀 Generate Blog Post", 
            type="primary",
            use_container_width=True
        )
    
    # Processing and results
    if generate_clicked and youtube_url:
        if not youtube_url.strip():
            st.error("Please enter a valid YouTube URL")
            return
            
        # Validate URL format
        if "youtube.com/watch" not in youtube_url and "youtu.be/" not in youtube_url:
            st.error("Please enter a valid YouTube URL")
            return
        
        try:
            # Show processing status
            with st.spinner("🔄 Processing your video..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("📥 Checking video accessibility...")
                progress_bar.progress(10)
                
                orchestrator = BlogOrchestrator()
                
                status_text.text("🎵 Extracting and validating transcript...")
                progress_bar.progress(30)
                
                start_time = time.time()
                
                # This will now FAIL FAST if transcript is invalid
                blog_data = asyncio.run(orchestrator.generate_blog_post(youtube_url))
                
                end_time = time.time()
                
                progress_bar.progress(90)
                status_text.text("✨ Finalizing blog post...")
                progress_bar.progress(100)
                status_text.empty()
            
            # Success! We have a real blog post
            processing_time = int(end_time - start_time)
            stats = blog_data.get("stats", {})
            word_count = stats.get("word_count", len(blog_data["content"].split()))
            
            # Show success with detailed stats
            st.markdown(f"""
            <div class="success-box">
                ✅ <strong>Blog post generated successfully!</strong><br>
                📊 Word count: {word_count:,} words<br>
                ⏱️ Processing time: {processing_time} seconds<br>
                📝 Transcript length: {stats.get('transcript_length', 0):,} characters<br>
                📅 Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            </div>
            """, unsafe_allow_html=True)
            
            # Show any worker issues (if any)
            failed_workers = stats.get("failed_workers", [])
            if failed_workers:
                st.markdown(f"""
                <div class="warning-box">
                    ⚠️ <strong>Note:</strong> Some sections had issues: {', '.join(failed_workers)}<br>
                    The blog post is still complete with the remaining sections.
                </div>
                """, unsafe_allow_html=True)
            
            # Display the blog post
            st.markdown('<div class="blog-container">', unsafe_allow_html=True)
            st.markdown("## 📖 Generated Blog Post")
            st.markdown(blog_data["content"])
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Download options
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col2:
                st.download_button(
                    label="📥 Download as Markdown",
                    data=blog_data["content"],
                    file_name=f"blog_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
        except RuntimeError as e:
            # These are our controlled errors with helpful messages
            error_msg = str(e)
            
            if "transcript" in error_msg.lower():
                st.markdown(f"""
                <div class="error-box">
                    🎥 <strong>Video Processing Issue:</strong><br>
                    {error_msg}<br><br>
                    <strong>Try these solutions:</strong><br>
                    • Choose a video with clear, audible speech<br>
                    • Ensure the video is public and accessible<br>
                    • Try a different video (educational content works best)<br>
                    • Check that yt-dlp is updated: <code>brew upgrade yt-dlp</code>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="error-box">
                    ❌ <strong>Processing Failed:</strong><br>
                    {error_msg}<br><br>
                    Please try again or choose a different video.
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            # Unexpected errors
            st.markdown(f"""
            <div class="error-box">
                ❌ <strong>Unexpected Error:</strong><br>
                {str(e)}<br><br>
                This is likely a system issue. Please try again in a few minutes.
            </div>
            """, unsafe_allow_html=True)
    
    elif generate_clicked:
        st.error("Please enter a YouTube URL first!")
    
    # Enhanced sidebar
    with st.sidebar:
        st.markdown("## ✅ Quality Guarantee")
        st.markdown("""
        **This system will NEVER generate placeholder content!**
        
        ✅ Real analysis of video content  
        ✅ Actual quotes from the video  
        ✅ Meaningful insights extracted  
        ❌ No generic templates  
        ❌ No placeholder text  
        """)
        
        st.markdown("## 🎯 Best Video Types")
        st.markdown("""
        - 📚 **Educational content**
        - 🎤 **Clear speech/interviews** 
        - 📱 **Tutorial videos**
        - 🗣️ **Presentations/talks**
        - 📺 **Documentary content**
        
        **Avoid:**
        - Music videos (no speech)
        - Very short clips (<2 minutes)
        - Poor audio quality
        - Private/restricted videos
        """)
        
        st.markdown("## 🔧 Troubleshooting")
        st.markdown("""
        **Error messages you might see:**
        
        🔴 "Cannot generate blog: No transcript content"
        → Video has no speech or is inaccessible
        
        🔴 "Transcript too short"  
        → Video is too brief for meaningful analysis
        
        🔴 "Missing required tools"
        → Run: `brew install yt-dlp ffmpeg`
        """)

if __name__ == "__main__":
    main()
