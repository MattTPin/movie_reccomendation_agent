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
            tmdb_api_key_input = gr.Textbox(label="TMDB API Key")
            tmdb_read_access_token_input = gr.Textbox(label="TMDB Read Access Token")
            omdb_api_key_input = gr.Textbox(label="OMDB API Key")
            trakt_client_id_input = gr.Textbox(label="Trakt Client ID")
            trakt_client_secret_input = gr.Textbox(label="Trakt Client Secret")
    else:
        # Local mode: use config.py
        tmdb_api_key_input = gr.Textbox(value=config.TMDB_API_KEY, visible=False)
        tmdb_read_access_token_input = gr.Textbox(value=config.TMDB_READ_ACCESS_TOKEN, visible=False)
        omdb_api_key_input = gr.Textbox(value=config.OMDB_API_KEY, visible=False)
        trakt_client_id_input = gr.Textbox(value=config.TRAKT_CLIENT_ID, visible=False)
        trakt_client_secret_input = gr.Textbox(value=config.TRAKT_CLIENT_SECRET, visible=False)

    return [
        tmdb_api_key_input,
        tmdb_read_access_token_input,
        omdb_api_key_input,
        trakt_client_id_input,
        trakt_client_secret_input,
    ]