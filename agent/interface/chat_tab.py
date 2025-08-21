# chat_tab.py
import json
import re
import gradio as gr
from agent.logic.router import route
from agent.logic.llm import invoke_claude  # ensure this is exposed

from agent.utils.media_extract import embed_links, extract_all_youtube_ids
from agent.interface.video_tab_interface import (
    get_trailer_html, next_trailer, prev_trailer, close_trailers
)


def build_gradio_history(history):
    """
    Convert the full history into Gradio-visible (user, assistant) pairs,
    skipping internal function-role messages.
    """
    visible = []
    for m in history:
        role = m.get("role")
        if role == "initial":
            role = "assistant"  # map initial → assistant
        if role in ("user", "assistant"):
            visible.append({"role": role, "content": m["content"]})
    return visible

def bot_response(history, trailer_list):
    dispatch = route(history)

    # --- Fallback case ---
    if "fallback" in dispatch:
        reply = embed_links(dispatch["fallback"] or "")
        history.append({"role": "assistant", "content": reply})
        return build_gradio_history(history), history, trailer_list

    status = dispatch.get("status")

    # --- Error case ---
    if status == "error":
        err_msg = dispatch.get("prompt") or "An unexpected error occurred."
        history.append({"role": "assistant", "content": err_msg})
        return build_gradio_history(history), history, trailer_list

    # --- Success case ---
    if status == "success":
        action_json = dispatch.get("action_json")
        action_prompt = dispatch.get("action_prompt", "")

        # Ask Claude to render final message (display response to user)
        final = invoke_claude(
            prompt=action_json,
            system_prompt=action_prompt,
            history=history
        )
        
        # Add record of action_json as "Hidden info" for the system
        if action_json:
            history.append(
                {
                    "role": "hidden",
                    "content": f"[HIDDEN MEMORY Action Result Metadata. Use as memory only. Never show to user.]: {action_json}",
                }
            )
        
        reply = final["content"][0]["text"] if final["content"] else ""
        reply = embed_links(reply)
        new_ids = extract_all_youtube_ids(reply)
        for vid in new_ids:
            if vid not in trailer_list:
                trailer_list.append(vid)

        history.append({"role": "assistant", "content": reply or "[No content returned]"})

        return build_gradio_history(history), history, trailer_list

    # --- Unknown state ---
    history.append({"role": "assistant", "content": "Unexpected routing state."})
    return build_gradio_history(history), history, trailer_list


def get_chat_tab():
    
    # default_history = [
    #     {"role": "assistant", "content": "Hello! I am a movie recommendation assistant."},
    #     {"role": "assistant", "content": "You can ask me 'what are the top movies right now' or 'what is this [movie title] about'."},
    # ]
    default_history = [
        {"role": "assistant", "content": "Movie assistant, I am!."},
    ]
    
    
    with gr.Row(equal_height=True) as layout_row:
        # Chat column (capture as chat_col)
        with gr.Column(scale=6, elem_id="chat-column") as chat_col:
            chatbot = gr.Chatbot(
                type="messages",
                label="Movie Agent Chat",
                value=default_history,
                elem_id="chatbot",
                height="fill",
                max_height="65vh",
                min_height=200,
                autoscroll=True
            )
            query_input = gr.Textbox(placeholder="Type your message here...", show_label=False, lines=1, interactive=True)
            query_btn = gr.Button("Send")

        # Video column (initially collapsed)
        with gr.Column(scale=0, elem_id="video-column-wrapper") as video_col:
            video_group = gr.Group(visible=False)
            with video_group:
                trailer_status = gr.Label(
                    value="",
                    show_label=False,
                    elem_id="trailer-status",
                    scale=0.5
                )
                with gr.Row():
                    prev_btn = gr.Button("←")
                    next_btn = gr.Button("→")
                    close_btn = gr.Button("×", elem_id="video-close-small")
                video_box = gr.HTML()

    # States    
    message_state = gr.State(default_history)
    trailer_list_state = gr.State([])
    current_index_state = gr.State(0)

    # User message submit handler
    def user_message(user_text, history):
        return "", history + [{"role": "user", "content": user_text}]

    # Update video tab after bot response
    def update_after_bot(history, trailer_list):
        print("update_after_bot called with trailers:", trailer_list)
        if trailer_list:
            html, idx, trailer_status = get_trailer_html(trailer_list, 0)
            return (
                html,
                idx,
                gr.update(visible=True),       # show video group
                trailer_list,
                gr.update(visible=True, scale=3),  # video col
                gr.update(visible=True, scale=3),  # chat col
                trailer_status
            )
        else:
            return (
                "",
                0,
                gr.update(visible=False),
                trailer_list,
                gr.update(visible=False),
                gr.update(visible=True, scale=6),
                ""
            )
    # Main query submission (Enter key)
    query_input.submit(
        user_message,
        inputs=[query_input, message_state],
        outputs=[query_input, message_state],
    ).then(
        bot_response,
        inputs=[message_state, trailer_list_state],
        outputs=[chatbot, message_state, trailer_list_state],
    ).then(
        update_after_bot,
        inputs=[message_state, trailer_list_state],
        outputs=[
            video_box,             # HTML with trailer
            current_index_state,   # new index
            video_group,           # show/hide sidebar group
            trailer_list_state,    # updated list
            video_col,             # sidebar column scale
            chat_col,              # ← chat column scale update
            trailer_status
        ],
    )

    # Submit by button
    query_btn.click(
        user_message,
        inputs=[query_input, message_state],
        outputs=[query_input, message_state],
    ).then(
        bot_response,
        inputs=[message_state, trailer_list_state],
        outputs=[chatbot, message_state, trailer_list_state],
    ).then(
        update_after_bot,
        inputs=[message_state, trailer_list_state],
        outputs=[
            video_box,             # HTML with trailer
            current_index_state,   # new index
            video_group,           # show/hide sidebar group
            trailer_list_state,    # updated list
            video_col,             # sidebar column scale
            chat_col,              # ← chat column scale update
            trailer_status,
        ],
    )

    # Video navigation buttons
    prev_btn.click(
        prev_trailer,
        inputs=[current_index_state, trailer_list_state],
        outputs=[video_box, current_index_state],
    )
    next_btn.click(
        next_trailer,
        inputs=[current_index_state, trailer_list_state],
        outputs=[video_box, current_index_state],
    )
    close_btn.click(
        close_trailers,
        outputs=[
            video_box,            # updated HTML
            current_index_state,  # reset index
            trailer_list_state,   # cleared list
            video_group,          # hide/show group
            chat_col,             # update chat_col scale
            video_col,            # update video_col scale
        ],
    )


    return [query_input, chatbot, query_btn, message_state, video_box, trailer_list_state, current_index_state]