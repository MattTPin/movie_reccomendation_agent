# video_tab_interface.py

import gradio as gr

from agent.utils.media_extract import youtube_iframe_html

def get_trailer_html(trailer_list, index):
    if not trailer_list or index < 0 or index >= len(trailer_list):
        return "", 0, ""
    return youtube_iframe_html(trailer_list[index]), index, get_trailer_status(index, trailer_list)

def next_trailer(index, trailer_list):
    if not trailer_list:
        return "", 0, ""
    new_index = (index + 1) % len(trailer_list)
    return youtube_iframe_html(trailer_list[new_index]), new_index, get_trailer_status(new_index, trailer_list)

def prev_trailer(index, trailer_list):
    if not trailer_list:
        return "", 0, ""
    new_index = (index - 1) % len(trailer_list)
    return youtube_iframe_html(trailer_list[new_index]), new_index, get_trailer_status(new_index, trailer_list)

def get_trailer_status(index, trailer_list):
    if not trailer_list:
        return ""
    return f"Trailer {index + 1} of {len(trailer_list)}"

def close_trailers():
    return (
        "",                        # video_box value
        0,                         # current_index_state
        [],                        # trailer_list_state
        gr.update(visible=False),  # hide video_group
        gr.update(scale=4),        # expand chat_col
        gr.update(scale=0),        # collapse video_col
        ""                         # clear trailer status
    )