# media_extract.py

import re

def embed_links(text: str) -> str:
    """
    Embed YouTube and image links as markdown-style links.
    """
    # Embed YouTube links
    text = re.sub(
        r'(https?://(?:www\.)?youtube\.com/watch\?v=([\w\-]+))',
        r'[Watch on YouTube](\1)',
        text,
    )
    # Embed image links
    text = re.sub(
        r'(https?://\S+\.(?:png|jpe?g|webp|gif))',
        r'![Image](\1)',
        text,
    )
    return text

def extract_all_youtube_ids(text: str) -> list[str]:
    return re.findall(r'https?://(?:www\.)?youtube\.com/watch\?v=([\w\-]+)', text)

def youtube_iframe_html(video_id: str) -> str:
    return f"""
    <iframe width="100%" height="315"
        src="https://www.youtube.com/embed/{video_id}"
        frameborder="0"
        allowfullscreen>
    </iframe>
    """
