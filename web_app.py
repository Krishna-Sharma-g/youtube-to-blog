#!/usr/bin/env python3
"""
YouTube Blog Generator - Streamlit Cloud Version
Properly structured with all code inside main() function
"""

import streamlit as st
import asyncio
import sys
from pathlib import Path
import os
import requests 
import time
from datetime import datetime
import logging

# Add src to path for imports
sys.path.append(str(Path(__file__).resolve().parent / "src"))

# Configure page
st.set_page_config(
    page_title="YouTube to Blog Generator",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main-header { text-align: center; color: #FF6B6B; font-size: 3rem; margin-bottom: 0.5rem; }
    .sub-header { text-align: center; color: #666; font-size: 1.2rem; margin-bottom: 2rem; }
    .success-box { background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0; }
    .error-box { background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0; }
    .warning-box { background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0; }
    .blog-container { background-color: #f8f9fa; padding: 2rem; border-radius: 1rem; border-left: 5px solid #FF6B6B; margin: 1rem 0; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def main():
    """Main Streamlit app function - all UI code goes here."""
    
    # Header
    st.markdown('<h1 class="main-header">🎬 → 📝</h1>', unsafe_allow_html=True)
    st.markdown('<h2 class="main-header">YouTube to Blog Generator</h2>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Transform YouTube videos into comprehensive blog posts - BULLETPROOF version!</p>', unsafe_allow_html=True)
    
    # Import orchestrator inside function to avoid module-level import errors
    try:
        from orchestrator import BlogOrchestrator
        orchestrator = BlogOrchestrator()
    except Exception as e:
        st.error(f"❌ Configuration Error: {str(e)}")
        st.info("Please check that all dependencies are installed and configured correctly.")
        return  # ✅ CORRECT: return is inside a function
    
    # Input section
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        youtube_url = st.text_input(
            "📎 Enter YouTube URL:",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Paste any YouTube video URL here",
            key="url_input"
        )
        
        generate_clicked = st.button(
            "🚀 Generate Blog Post", 
            type="primary",
            use_container_width=True
        )
    
    # Processing section
    if generate_clicked and youtube_url:
        if not youtube_url.strip():
            st.error("Please enter a valid YouTube URL")
            return  # ✅ CORRECT: return is inside a function
            
        # Validate URL format
        if "youtube.com/watch" not in youtube_url and "youtu.be/" not in youtube_url:
            st.error("Please enter a valid YouTube URL")
            return  # ✅ CORRECT: return is inside a function
        
        try:
            # Show processing status
            with st.spinner("🔄 Processing your video..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("📥 Initializing bulletproof processor...")
                progress_bar.progress(10)
                
                status_text.text("🎵 Extracting content with multiple fallbacks...")
                progress_bar.progress(30)
                
                start_time = time.time()
                blog_data = asyncio.run(orchestrator.generate_blog_post(youtube_url))
                end_time = time.time()
                
                progress_bar.progress(90)
                status_text.text("✨ Finalizing content...")
                progress_bar.progress(100)
                status_text.empty()
            
            # Check if emergency mode was used
            is_emergency = blog_data.get("stats", {}).get("emergency_mode", False)
            
            if is_emergency:
                st.markdown(f"""
                <div class="warning-box">
                    ⚠️ <strong>Limited Processing Mode:</strong><br>
                    We encountered challenges processing this specific video, but generated content based on available information.<br><br>
                    <strong>For better results, try:</strong><br>
                    • A video with clear speech and captions<br>
                    • Educational or tutorial content<br>
                    • Videos longer than 5 minutes
                </div>
                """, unsafe_allow_html=True)
            
            # Show success message
            processing_time = int(end_time - start_time)
            stats = blog_data.get("stats", {})
            word_count = stats.get("word_count", len(blog_data["content"].split()))
            success_rate = stats.get("success_rate", "unknown")
            
            st.markdown(f"""
            <div class="success-box">
                ✅ <strong>Blog post generated successfully!</strong><br>
                📊 Word count: {word_count:,} words<br>
                ⏱️ Processing time: {processing_time} seconds<br>
                🎯 Success rate: {success_rate} sections<br>
                📅 Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            </div>
            """, unsafe_allow_html=True)
            
            # Display the blog post
            st.markdown('<div class="blog-container">', unsafe_allow_html=True)
            st.markdown("## 📖 Generated Blog Post")
            st.markdown(blog_data["content"])
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Download button
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                st.download_button(
                    label="📥 Download as Markdown",
                    data=blog_data["content"],
                    file_name=f"blog_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
        
        except Exception as e:
            st.markdown(f"""
            <div class="error-box">
                ❌ <strong>Processing Error:</strong><br>
                {str(e)}<br><br>
                Please try a different video or contact support if this persists.
            </div>
            """, unsafe_allow_html=True)
    
    elif generate_clicked:
        st.error("Please enter a YouTube URL first!")
    
    # Sidebar with information
    with st.sidebar:
        st.markdown("## ✅ Quality Guarantee")
        st.markdown("""
        **This system will NEVER completely fail!**
        
        ✅ Multiple extraction strategies  
        ✅ Safe worker processing  
        ✅ Emergency fallback content  
        ✅ Bulletproof error handling  
        """)
        
        st.markdown("## 🎯 Best Video Types")
        st.markdown("""
        - 📚 **Educational content**
        - 🎤 **Clear speech/interviews** 
        - 📱 **Tutorial videos**
        - 🗣️ **Presentations/talks**
        - 📺 **Documentary content**
        """)
        
        st.markdown("## 🧪 Test Videos")
        test_videos = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=8S0FDjFBj8o",
            "https://www.youtube.com/watch?v=ZmAzIqRSYIM"
        ]
        
        for i, test_url in enumerate(test_videos, 1):
            if st.button(f"Test Video {i}", key=f"test_{i}"):
                st.session_state.url_input = test_url
                st.experimental_rerun()
                # Add this test function to your web_app.py
# Replace the test_openai_connection function with this:
# Replace the test_openai_connection function with this:
def test_openai_connection_sync():
    """Test OpenAI API connectivity using requests."""
    try:
        # Get API key
        try:
            api_key = st.secrets["OPENAI_API_KEY"]
        except:
            api_key = os.getenv("OPENAI_API_KEY")
            
        if not api_key or not api_key.startswith("sk-"):
            return False, "OpenAI API key not found or invalid format"
        
        # Test API call
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Say 'test successful'"}],
            "max_tokens": 10
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            return True, "OpenAI API working perfectly!"
        else:
            return False, f"API Error {response.status_code}: {response.text[:200]}"
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"

# Update the button to use sync function:
if st.button("🧪 Test OpenAI Connection"):
    with st.spinner("Testing OpenAI API..."):
        is_working, message = test_openai_connection_sync()
        if is_working:
            st.success(f"✅ {message}")
        else:
            st.error(f"❌ {message}")

# ✅ CORRECT: Entry point that calls main function
if __name__ == "__main__":
    main()
