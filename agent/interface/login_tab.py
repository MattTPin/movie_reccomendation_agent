# login_tab.py

import gradio as gr
from agent import config

import os
DEPLOYED = os.getenv("DEPLOYED", "False") == "False"


# def login_trakt(client_id):
#     url = get_oauth_url(client_id=client_id)
#     return f"1. Visit: {url}\n2. Authorize and paste the returned code below."


# def submit_code(code, client_id, client_secret):
#     token_data = exchange_code_for_token(code, client_id=client_id, client_secret=client_secret)
#     return token_data["access_token"]


def get_login_tab():
    if DEPLOYED:
        with gr.Tab("Step 1: Enter API Keys"):
            trakt_client_id_input = gr.Textbox(label="Trakt Client ID")
            trakt_client_secret_input = gr.Textbox(label="Trakt Client Secret")
    else:
        # Local mode: use config.py
        trakt_client_id_input = gr.Textbox(value=config.TRAKT_CLIENT_ID, visible=False)
        trakt_client_secret_input = gr.Textbox(value=config.TRAKT_CLIENT_SECRET, visible=False)

    return [
        trakt_client_id_input,
        trakt_client_secret_input,
    ]