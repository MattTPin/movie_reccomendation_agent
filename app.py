# app.py

import os
import gradio as gr
from dotenv import load_dotenv


# Load .env for local
load_dotenv()

from agent.interface.chat_tab import get_chat_tab
from agent.interface.login_tab import get_login_tab


from agent import config


with gr.Blocks(
    css="""
        /* Make chatbot fill available vertical space */
        .gradio-container .chatbot {
            height: calc(100vh - 250px) !important;
            max-height: none !important;
        }
        .gradio-container .column {
            min-width: 0 !important;
            flex-basis: 0 !important;
        }
        #video-column-wrapper {
            transition: all 0.3s ease;
            min-width: 0 !important;
            max-width: 400px;  /* or however wide you want */
        }
        #video-column-wrapper[style*="display: none"] {
            display: none !important;
            max-width: 0px;  
            width: 0 !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        #video-column {
            transition: all 0.3s ease;
        }
        #chat-column {
            flex-grow: 5 !important;
            max-width: 100% !important;
            min-width: 0 !important;  /* allow shrinking if needed */
            transition: all 0.3s ease;
        }
        #trailer-status {
            font-size: 6px; /* Adjust the size as needed */
        }
    """
) as demo:
    
    gr.Markdown("# 🎬 Movie Agent")

    get_login_tab()
    with gr.Tab("Step 2: Chat + Trakt Setup"):
        get_chat_tab()

demo.launch()
