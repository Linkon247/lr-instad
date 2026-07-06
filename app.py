"""
LR InstaD 📥 - Instagram Video Downloader
A single-file Streamlit application.

Run with:
    pip install streamlit yt-dlp requests
    streamlit run app.py
"""

import re
import io
import requests
import streamlit as st
import yt_dlp

# --------------------------------------------------------------------------
# Page configuration
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="LR InstaD",
    page_icon="📥",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --------------------------------------------------------------------------
# Custom CSS - dark mode with an Instagram-style purple/pink gradient
# --------------------------------------------------------------------------
st.markdown(
    """
    <style>
        /* Hide default Streamlit chrome */
        #MainMenu, footer, header {visibility: hidden;}

        .stApp {
            background: radial-gradient(circle at top, #1e1130 0%, #120a1e 55%, #0a0612 100%);
            color: #f5f3f7;
        }

        .block-container {
            padding-top: 6rem;
            max-width: 640px;
        }

        /* Title block */
        .lr-title-wrap {
            text-align: center;
            margin-bottom: 0.2rem;
        }
        .lr-icon {
            font-size: 3.2rem;
            line-height: 1;
            filter: drop-shadow(0 0 14px rgba(214, 74, 189, 0.55));
        }
        .lr-title {
            font-size: 2.4rem;
            font-weight: 800;
            letter-spacing: 0.5px;
            background: linear-gradient(90deg, #f9ce34 0%, #ee2a7b 40%, #6228d7 100%);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            margin: 0.2rem 0 0.1rem 0;
        }
        .lr-subtitle {
            text-align: center;
            color: #b4a9c4;
            font-size: 0.95rem;
            margin-bottom: 2.2rem;
        }

        /* Text input styling */
        div[data-testid="stTextInput"] input {
            background-color: #1c1229;
            border: 1.5px solid #3a2a52;
            border-radius: 14px;
            padding: 0.85rem 1rem;
            color: #ffffff;
            font-size: 1rem;
        }
        div[data-testid="stTextInput"] input:focus {
            border-color: #ee2a7b;
            box-shadow: 0 0 0 3px rgba(238, 42, 123, 0.25);
        }
        div[data-testid="stTextInput"] input::placeholder {
            color: #7c6f8d;
        }

        /* Primary button */
        div.stButton > button {
            width: 100%;
            background: linear-gradient(90deg, #f9ce34 0%, #ee2a7b 45%, #6228d7 100%);
            color: #ffffff;
            border: none;
            border-radius: 14px;
            padding: 0.85rem 1rem;
            font-size: 1.05rem;
            font-weight: 700;
            letter-spacing: 0.3px;
            margin-top: 0.6rem;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        div.stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 22px rgba(238, 42, 123, 0.35);
            color: #ffffff;
            border: none;
        }
        div.stButton > button:active {
            transform: translateY(0px);
        }

        /* Download button (post-fetch) */
        div[data-testid="stDownloadButton"] > button {
            width: 100%;
            background: #1c1229;
            border: 1.5px solid #6228d7;
            color: #ffffff;
            border-radius: 14px;
            padding: 0.8rem 1rem;
            font-weight: 700;
            font-size: 1rem;
        }
        div[data-testid="stDownloadButton"] > button:hover {
            border-color: #ee2a7b;
            color: #ffffff;
        }

        .lr-footer {
            text-align: center;
            color: #5f5470;
            font-size: 0.8rem;
            margin-top: 2.5rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
st.markdown(
    """
    <div class="lr-title-wrap">
        <div class="lr-icon">📥</div>
        <div class="lr-title">LR InstaD</div>
    </div>
    <div class="lr-subtitle">Paste a public Instagram video link and download the MP4 instantly.</div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------
if "video_bytes" not in st.session_state:
    st.session_state.video_bytes = None
if "video_filename" not in st.session_state:
    st.session_state.video_filename = None
if "video_title" not in st.session_state:
    st.session_state.video_title = None

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
INSTAGRAM_URL_PATTERN = re.compile(
    r"^https?://(www\.)?instagram\.com/(reel|reels|p|tv)/[A-Za-z0-9_\-]+/?",
    re.IGNORECASE,
)


def is_valid_instagram_url(url: str) -> bool:
    return bool(INSTAGRAM_URL_PATTERN.match(url.strip()))


def fetch_video(url: str):
    """
    Uses yt-dlp to resolve the direct MP4 URL for the given Instagram link,
    then streams the raw bytes back so Streamlit can offer them for download.
    Raises RuntimeError with a clean message on any failure.
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": "mp4/best[ext=mp4]/best",
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError:
        raise RuntimeError("Invalid Link or Private Video!")
    except Exception:
        raise RuntimeError("Invalid Link or Private Video!")

    if not info:
        raise RuntimeError("Invalid Link or Private Video!")

    # Resolve the direct media URL (handles both flat and 'formats' responses)
    direct_url = info.get("url")
    if not direct_url:
        formats = info.get("formats") or []
        mp4_formats = [f for f in formats if f.get("ext") == "mp4" and f.get("url")]
        chosen = mp4_formats[-1] if mp4_formats else (formats[-1] if formats else None)
        direct_url = chosen.get("url") if chosen else None

    if not direct_url:
        raise RuntimeError("Invalid Link or Private Video!")

    try:
        response = requests.get(direct_url, stream=True, timeout=30)
        response.raise_for_status()
    except requests.RequestException:
        raise RuntimeError("Invalid Link or Private Video!")

    buffer = io.BytesIO()
    for chunk in response.iter_content(chunk_size=1024 * 256):
        if chunk:
            buffer.write(chunk)
    buffer.seek(0)

    title = info.get("title") or info.get("id") or "instagram_video"
    safe_title = re.sub(r"[^A-Za-z0-9_\-]+", "_", title)[:60] or "instagram_video"

    return buffer.getvalue(), f"{safe_title}.mp4", title


# --------------------------------------------------------------------------
# Main UI
# --------------------------------------------------------------------------
url = st.text_input(
    label="Instagram link",
    placeholder="Paste your Instagram video link here...",
    label_visibility="collapsed",
)

download_clicked = st.button("📥 Download Video")

if download_clicked:
    st.session_state.video_bytes = None
    st.session_state.video_filename = None
    st.session_state.video_title = None

    cleaned_url = url.strip()

    if not cleaned_url:
        st.error("Please paste an Instagram video link first.")
    elif not is_valid_instagram_url(cleaned_url):
        st.error("Invalid Link or Private Video!")
    else:
        try:
            with st.spinner("Fetching video..."):
                video_bytes, filename, title = fetch_video(cleaned_url)
            st.session_state.video_bytes = video_bytes
            st.session_state.video_filename = filename
            st.session_state.video_title = title
            st.success(f"Video ready: {title}")
        except RuntimeError as e:
            st.error(str(e))
        except Exception:
            st.error("Invalid Link or Private Video!")

if st.session_state.video_bytes:
    st.download_button(
        label="⬇️ Save MP4 to Device",
        data=st.session_state.video_bytes,
        file_name=st.session_state.video_filename,
        mime="video/mp4",
    )

st.markdown(
    '<div class="lr-footer">LR InstaD — for personal, non-commercial use only. '
    "Only download videos you have the right to save.</div>",
    unsafe_allow_html=True,
)
