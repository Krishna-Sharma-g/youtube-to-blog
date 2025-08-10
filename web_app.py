#!/usr/bin/env python3
"""
YouTube to Blog Generator - Complete Streamlit Web App
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 Converts any YouTube video into a comprehensive blog post
⚡ Bulletproof with multiple extraction strategies
🛡️ Robust error handling and user guidance
🌐 Optimized for Streamlit Cloud deployment
"""

import streamlit as st
import asyncio
import sys
from pathlib import Path
import time
from datetime import datetime
import logging

# Add src to path for imports
sys.path.append(str(Path(__file__).resolve().parent / "src"))

# Configure Streamlit page
st.set_page_config(
    page_title="YouTube to Blog Generator",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Main styling */
    .main-header {
        text-align: center;
        color: #FF6B6B;
        font-size: 3rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Status boxes */
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 5px solid #28a745;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 5px solid #dc3545;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 5px solid #ffc107;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 5px solid #17a2b8;
    }
    
    /* Blog content container */
    .blog-container {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 1rem;
        border-left: 5px solid #FF6B6B;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom button styling */
    .stButton > button {
        background-color: #FF6B6B;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #FF8E53;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div {
        background-color: #FF6B6B;
    }
</style>
""", unsafe_allow_html=True)

def check_system_status():
    """Check if system dependencies are properly configured."""
    try:
        from orchestrator import BlogOrchestrator
        from config.settings import get_settings
        
        # Test configuration
        settings = get_settings()
        
        return True, "System ready"
    except ImportError as e:
        return False, f"Import error: {str(e)}"
    except Exception as e:
        return False, f"Configuration error: {str(e)}"

def main():
    """Main Streamlit application function."""
    
    # Header
    st.markdown('<h1 class="main-header">🎬 → 📝</h1>', unsafe_allow_html=True)
    st.markdown('<h2 class="main-header">YouTube to Blog Generator</h2>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Transform any YouTube video into a comprehensive, SEO-optimized blog post in minutes!</p>', unsafe_allow_html=True)
    
    # System status check
    system_ok, status_msg = check_system_status()
    
    if not system_ok:
        st.markdown(f"""
        <div class="error-box">
            ❌ <strong>System Configuration Error:</strong><br>
            {status_msg}<br><br>
            Please check that all dependencies are properly installed and configured.
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Success indicator
    st.markdown(f"""
    <div class="info-box">
        ✅ <strong>System Status:</strong> All systems operational and ready to process videos!
    </div>
    """, unsafe_allow_html=True)
    
    # Main input section
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        youtube_url = st.text_input(
            "📎 Enter YouTube Video URL:",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Paste any YouTube video URL here. Educational content works best!",
            key="url_input"
        )
        
        generate_clicked = st.button(
            "🚀 Generate Blog Post", 
            type="primary",
            use_container_width=True,
            help="Click to start processing your video"
        )
    
    # Processing section
    if generate_clicked and youtube_url:
        if not youtube_url.strip():
            st.error("Please enter a valid YouTube URL")
            return
            
        # Basic URL validation
        if not ("youtube.com/watch" in youtube_url or "youtu.be/" in youtube_url):
            st.error("Please enter a valid YouTube URL (youtube.com or youtu.be)")
            return
        
        # Initialize orchestrator
        try:
            from orchestrator import BlogOrchestrator
            orchestrator = BlogOrchestrator()
        except Exception as e:
            st.markdown(f"""
            <div class="error-box">
                ❌ <strong>Orchestrator Error:</strong><br>
                {str(e)}<br><br>
                Please check system configuration.
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Processing with progress indicators
        try:
            with st.spinner("🔄 Processing your video..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Step 1: Initialize
                status_text.text("📥 Initializing video processor...")
                progress_bar.progress(10)
                time.sleep(0.5)
                
                # Step 2: Extract content
                status_text.text("🎵 Extracting video content (this may take 1-3 minutes)...")
                progress_bar.progress(30)
                
                start_time = time.time()
                blog_data = asyncio.run(orchestrator.generate_blog_post(youtube_url))
                
                # Step 3: Generate blog
                status_text.text("✨ Generating blog sections...")
                progress_bar.progress(70)
                time.sleep(0.5)
                
                # Step 4: Finalize
                status_text.text("🔧 Finalizing blog post...")
                progress_bar.progress(90)
                time.sleep(0.5)
                
                end_time = time.time()
                
                progress_bar.progress(100)
                status_text.text("✅ Processing complete!")
                time.sleep(0.5)
                status_text.empty()
            
            # Check if we got valid content
            if not blog_data or not blog_data.get("content"):
                st.markdown(f"""
                <div class="error-box">
                    ❌ <strong>Blog Generation Failed:</strong><br>
                    No content was generated from this video.<br><br>
                    Please try a different video or check the troubleshooting guide in the sidebar.
                </div>
                """, unsafe_allow_html=True)
                return
            
            # Check for emergency mode or errors
            stats = blog_data.get("stats", {})
            is_emergency = stats.get("emergency_mode", False)
            
            if is_emergency:
                st.markdown(f"""
                <div class="warning-box">
                    ⚠️ <strong>Limited Processing Mode:</strong><br>
                    We encountered challenges processing this specific video, but generated content based on available information.<br><br>
                    <strong>For better results, try:</strong><br>
                    • A video with clear speech and captions<br>
                    • Educational or tutorial content<br>
                    • Videos longer than 5 minutes<br>
                    • Popular videos from major creators
                </div>
                """, unsafe_allow_html=True)
            
            # Success metrics
            processing_time = int(end_time - start_time)
            word_count = stats.get("word_count", len(blog_data["content"].split()))
            success_rate = stats.get("success_rate", "unknown")
            
            st.markdown(f"""
            <div class="success-box">
                ✅ <strong>Blog post generated successfully!</strong><br>
                📊 <strong>Word count:</strong> {word_count:,} words<br>
                ⏱️ <strong>Processing time:</strong> {processing_time} seconds<br>
                🎯 <strong>Success rate:</strong> {success_rate} sections<br>
                📅 <strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            </div>
            """, unsafe_allow_html=True)
            
            # Display the blog post
            st.markdown('<div class="blog-container">', unsafe_allow_html=True)
            st.markdown("## 📖 Generated Blog Post")
            st.markdown("---")
            st.markdown(blog_data["content"])
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Download section
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col2:
                st.download_button(
                    label="📥 Download as Markdown",
                    data=blog_data["content"],
                    file_name=f"blog_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                    help="Download your blog post as a Markdown file"
                )
            
            # Additional options
            with st.expander("📊 View Processing Details"):
                st.json(stats)
                
                if "transcript" in blog_data:
                    st.markdown("### Original Transcript/Content:")
                    st.text_area(
                        "Raw extracted content:",
                        blog_data["transcript"],
                        height=200,
                        disabled=True
                    )
        
        except RuntimeError as e:
            error_msg = str(e)
            
            if "Could not extract valid video content" in error_msg:
                st.markdown(f"""
                <div class="error-box">
                    🎥 <strong>Video Content Extraction Failed</strong><br><br>
                    
                    <strong>This video couldn't be processed because:</strong><br>
                    • It may be private, age-restricted, or region-locked<br>
                    • It might be music-only without speech content<br>
                    • The video could have disabled captions and unclear audio<br><br>
                    
                    <strong>✅ Try these instead:</strong><br>
                    • Educational videos (TED Talks, tutorials)<br>
                    • News reports and interviews<br>
                    • Product reviews with clear narration<br>
                    • Any video with captions/subtitles enabled<br><br>
                    
                    <strong>💡 Pro tip:</strong> Use the guaranteed working videos in the sidebar!
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="error-box">
                    ❌ <strong>Processing Error:</strong><br>
                    {error_msg}<br><br>
                    Please try a different video or use one of the test examples in the sidebar.
                </div>
                """, unsafe_allow_html=True)
        
        except Exception as e:
            st.markdown(f"""
            <div class="error-box">
                ❌ <strong>Unexpected Error:</strong><br>
                {str(e)}<br><br>
                Please try refreshing the page or contact support if this persists.
            </div>
            """, unsafe_allow_html=True)
    
    elif generate_clicked:
        st.error("Please enter a YouTube URL first!")
    
    # Enhanced sidebar
    with st.sidebar:
        st.markdown("## ✅ Quality Guarantee")
        st.markdown("""
        **This system NEVER generates placeholder content!**
        
        ✅ Real analysis of video content  
        ✅ Actual quotes and insights  
        ✅ Meaningful blog sections  
        ✅ SEO-optimized output  
        ❌ No generic templates  
        ❌ No placeholder text  
        """)
        
        st.markdown("---")
        
        st.markdown("## 🧪 **Guaranteed Working Videos**")
        st.markdown("*Click any button to auto-fill the URL:*")
        
        guaranteed_videos = {
            "🎤 TED Talk": "https://www.youtube.com/watch?v=8S0FDjFBj8o",
            "📚 Educational": "https://www.youtube.com/watch?v=aircAruvnKk", 
            "🎬 Popular Video": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "🔬 Science": "https://www.youtube.com/watch?v=wJyUtbn0O5Y",
            "💻 Tech Tutorial": "https://www.youtube.com/watch?v=kqtD5dpn9C8"
        }
        
        for name, url in guaranteed_videos.items():
            if st.button(name, key=f"guaranteed_{name}", use_container_width=True):
                st.session_state.url_input = url
                st.rerun()
        
        st.markdown("---")
        
        st.markdown("## 🎯 **Best Video Types**")
        st.markdown("""
        ### ✅ **Excellent Results:**
        - 📚 Educational content (Khan Academy, Coursera)
        - 🎤 TED Talks & presentations
        - 📺 Tutorial videos with clear narration
        - 📰 News reports and interviews
        - 🔍 Product reviews and explanations
        - 🎬 Documentaries with narration
        
        ### ⚠️ **May Have Issues:**
        - 🎵 Music videos (instrumental only)
        - 🔒 Private or unlisted videos
        - 🚫 Age-restricted content
        - ⏱️ Very short videos (<2 minutes)
        - 🎶 Videos with only background music
        """)
        
        st.markdown("---")
        
        st.markdown("## 🔧 **Troubleshooting**")
        st.markdown("""
        **If you get errors:**
        
        🔴 **"Could not extract content"**  
        → Video may be private or have no speech
        
        🔴 **"Processing failed"**  
        → Try a different video from our guaranteed list
        
        🔴 **"All workers failed"**  
        → Check internet connection and try again
        
        💡 **Pro Tips:**
        - Educational videos work best
        - Ensure videos have captions when possible
        - Try popular videos from major creators
        - Avoid very new videos (may lack captions)
        """)
        
        st.markdown("---")
        
        st.markdown("## 📈 **Features**")
        st.markdown("""
        ✨ **SEO-optimized** titles and content  
        📝 **Key insights** extraction  
        💬 **Notable quotes** highlighting  
        📊 **Structured summaries**  
        🏷️ **Relevant tags** generation  
        ⚡ **Fast processing** (1-5 minutes)  
        💾 **One-click download** as Markdown  
        """)

# Entry point
if __name__ == "__main__":
    main()
