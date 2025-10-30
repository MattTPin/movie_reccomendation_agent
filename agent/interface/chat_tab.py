import os
import uuid

import gradio as gr
from langchain_anthropic.chat_models import ChatAnthropic
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

from agent.movie_agent import movie_agent_runnable

session_id = str(uuid.uuid4())

# --- Multi-session memory ---
SESSION_HISTORY = []

# --- Chat tab ---
def get_chat_tab():
    """
    Returns a Gradio chat tab component ready for multi-agent orchestration.
    Uses a single LLM client now (Anthropic Claude), but can later be
    replaced with a RunnableMap for multiple agents.
    """

    # --- Gradio UI ---
    with gr.Column(scale=5, elem_id="chat-column"):
        chatbot = gr.Chatbot()
        message = gr.Textbox(
            placeholder="Type your message here...",
            show_label=False,
            lines=1,
            elem_id="chat-input",
            interactive=True
        )
        submit_btn = gr.Button("Send")
        status_text = gr.HTML(value="", elem_id="status-text")

        # --- Message processing ---

        def process_message(user_message, gradio_history_list):
            if not user_message.strip():
                return gradio_history_list, "", ""

            # Append user message to
            SESSION_HISTORY.append(HumanMessage(content=user_message))

            # --- Call LLM with 6 messages of memory ---
            ai_resp = movie_agent_runnable.invoke(SESSION_HISTORY[-6:])

            # --- Append AI response to memory ---
            SESSION_HISTORY.append(ai_resp)

            # --- Update Gradio chat history ---
            gradio_history_list.append((user_message, ai_resp.content))

            return gradio_history_list, "", ""
        # Prebuilt I/O for reuse
        inputs = [message, chatbot]
        outputs = [chatbot, message, status_text]

        # Bind both "Send" button and Enter key submission
        submit_btn.click(fn=process_message, inputs=inputs, outputs=outputs)
        message.submit(fn=process_message, inputs=inputs, outputs=outputs)

    return


# OLD BEDROCK VERSION
# TODO: PORT OVER TRAILER SIDEBAR

# import json
# import re
# import gradio as gr
# from typing import List, Tuple
# from agent.logic.router import route
# from agent.utils.media_extract import embed_links, extract_all_youtube_ids
# from agent.interface.video_tab_interface import (
#     get_trailer_html, next_trailer, prev_trailer, close_trailers
# )
# from agent.logic.llm_client import LLMClient
# from agent.errors import LLMInitializationError

# # --- LangChain integration ---
# from langchain_core.runnables.history import RunnableWithMessageHistory
# from langchain.messages import HumanMessage, AIMessage


# def bot_response_wrapper(lc_memory, chatbot_history, trailer_list):
#     """
#     Generate bot reply and update chatbot and memory.
#     """
#     llm_client = LLMClient()
#     lc_memory, trailer_list = bot_response(
#         lc_memory.chat_memory.messages[-1].content,  # last user input
#         llm_client,
#         lc_memory,
#         trailer_list
#     )
#     ai_reply = lc_memory.chat_memory.messages[-1].content
#     chatbot_history = chatbot_history + [{"role": "assistant", "content": ai_reply}]
#     return lc_memory, chatbot_history, trailer_list

# # --- MAIN BOT LOGIC ---
# def bot_response(
#     user_text: str,
#     llm_client: LLMClient,
#     lc_memory: RunnableWithMessageHistory,
#     trailer_list: List[str]
# ) -> Tuple[RunnableWithMessageHistory, List[str]]:
#     """
#     Main bot response logic using LangChain memory and router integration.
#     """
#     # --- Route the user input ---
#     dispatch = route(
#         user_prompt=user_text,
#         lc_memory=lc_memory,
#         llm_client=llm_client
#     )

#     # --- Handle Fallbacks ---
#     if "fallback" in dispatch:
#         reply = embed_links(dispatch["fallback"] or "")
#         lc_memory.chat_memory.add_message(AIMessage(content=reply))
#         return lc_memory, trailer_list

#     # --- Handle Errors ---
#     if dispatch.get("status") == "error":
#         err_msg = dispatch.get("prompt", "An unexpected error occurred.")
#         lc_memory.chat_memory.add_message(AIMessage(content=err_msg))
#         return lc_memory, trailer_list

#     # --- Handle Success ---
#     if dispatch.get("status") == "success":
#         action_json = dispatch.get("action_json", "")
#         action_prompt = dispatch.get("action_prompt", "")

#         # Call the LLM client for the actual response
#         reply, token_count = llm_client.query(
#             system_prompt=action_prompt,
#             user_prompt=action_json,
#             lc_memory=lc_memory
#         )

#         reply = embed_links(reply)

#         # --- Extract any YouTube links ---
#         new_ids = extract_all_youtube_ids(reply)
#         for vid in new_ids:
#             if vid not in trailer_list:
#                 trailer_list.append(vid)

#         # --- Store bot response in memory ---
#         lc_memory.chat_memory.add_message(AIMessage(content=reply))

#         return lc_memory, trailer_list

#     # --- Unknown / Unexpected State ---
#     lc_memory.chat_memory.add_message(AIMessage(content="Unexpected routing state."))
#     return lc_memory, trailer_list


# # --- CHAT TAB / UI ---
# def get_chat_tab():
#     # Initiate the LLM client (catches invalid config)
#     llm_client = LLMClient()
#     try:
#         llm_client.test_connection()
#         llm_init_success = True
#     except LLMInitializationError:
#         llm_init_success = False
    
#     if llm_init_success:
#         # Define all initial assistant messages
#         default_msgs = [
#             AIMessage(content="Movie assistant, I am!"),
#             AIMessage(content="I can help process requests to manage entries in your Trakt.tv account."),
#         ]
#     else:
#         default_msgs = [
#             AIMessage(content=(
#                 "Failed to initiate LLM connection. Please ensure you have selected a valid combination of ",
#                 "provider and model and have provided a valid API key for your selected provider."
#             ))
#         ]

#     # Initialize LangChain memory
#     lc_memory = RunnableWithMessageHistory(
#         memory_key="chat_history",
#         return_messages=True
#     )
#     for msg in default_msgs:
#         lc_memory.chat_memory.add_message(msg)

#     # Extract visible messages for Gradio Chatbot
#     default_visible_history = [
#         {
#             "role": "assistant",
#             "content": msg.content
#         } for msg in default_msgs
#     ]

#     with gr.Row(equal_height=True) as layout_row:
#         with gr.Column(scale=6, elem_id="chat-column") as chat_col:
#             chatbot = gr.Chatbot(
#                 type="messages",
#                 label="Movie Agent Chat",
#                 value=default_visible_history,
#                 elem_id="chatbot",
#                 height="fill",
#                 max_height="65vh",
#                 min_height=200,
#                 autoscroll=True
#             )
#             query_input = gr.Textbox(
#                 placeholder="Type your message here...",
#                 show_label=False,
#                 lines=1,
#                 interactive=True
#             )
#             query_btn = gr.Button("Send")

#         with gr.Column(scale=0, elem_id="video-column-wrapper") as video_col:
#             video_group = gr.Group(visible=False)
#             with video_group:
#                 trailer_status = gr.Label(value="", show_label=False, elem_id="trailer-status", scale=0.5)
#                 with gr.Row():
#                     prev_btn = gr.Button("←")
#                     next_btn = gr.Button("→")
#                     close_btn = gr.Button("×", elem_id="video-close-small")
#                 video_box = gr.HTML()

#     # --- States ---
#     lc_memory_state = gr.State(lc_memory)
#     trailer_list_state = gr.State([])
#     current_index_state = gr.State(0)

#     def user_message(user_text, lc_memory, chatbot_history):
#         """
#         Add user message to LangChain memory and display in UI.
#         """
#         if not user_text.strip():
#             return "", lc_memory, chatbot_history

#         lc_memory.chat_memory.add_message(HumanMessage(content=user_text))
#         chatbot_history = chatbot_history + [{"role": "user", "content": user_text}]
#         return "", lc_memory, chatbot_history

#     def update_after_bot(lc_memory, trailer_list):
#         """
#         Refresh trailer display after bot reply.
#         """
#         print("update_after_bot called with trailers:", trailer_list)
#         if trailer_list:
#             html, idx, trailer_status = get_trailer_html(trailer_list, 0)
#             return (
#                 html,
#                 idx,
#                 gr.update(visible=True),
#                 trailer_list,
#                 gr.update(visible=True, scale=3),
#                 gr.update(visible=True, scale=3),
#                 trailer_status
#             )
#         else:
#             return (
#                 "",
#                 0,
#                 gr.update(visible=False),
#                 trailer_list,
#                 gr.update(visible=False),
#                 gr.update(visible=True, scale=6),
#                 ""
#             )

#     chatbot_state = gr.State(default_visible_history)

#     # --- User message submission (Enter key) ---
#     query_input.submit(
#         user_message,
#         inputs=[query_input, lc_memory_state, chatbot_state],
#         outputs=[query_input, lc_memory_state, chatbot_state],
#     ).then(
#         bot_response_wrapper,
#         inputs=[lc_memory_state, chatbot_state, trailer_list_state],
#         outputs=[lc_memory_state, chatbot_state, trailer_list_state],
#     ).then(
#         update_after_bot,
#         inputs=[lc_memory_state, trailer_list_state],
#         outputs=[
#             video_box,
#             current_index_state,
#             video_group,
#             trailer_list_state,
#             video_col,
#             chat_col,
#             trailer_status,
#         ],
#     )

#     # --- Submit via button ---
#     query_btn.click(
#         user_message,
#         inputs=[query_input, lc_memory_state, chatbot_state],
#         outputs=[query_input, lc_memory_state, chatbot_state],
#     ).then(
#         bot_response_wrapper,
#         inputs=[lc_memory_state, chatbot_state, trailer_list_state],
#         outputs=[lc_memory_state, chatbot_state, trailer_list_state],
#     ).then(
#         update_after_bot,
#         inputs=[lc_memory_state, trailer_list_state],
#         outputs=[
#             video_box,
#             current_index_state,
#             video_group,
#             trailer_list_state,
#             video_col,
#             chat_col,
#             trailer_status,
#         ],
#     )
    
#     # Wire chatbot_state to the visible chatbot
#     chatbot_state.change(lambda x: x, inputs=chatbot_state, outputs=chatbot)

#     # --- Video navigation ---
#     prev_btn.click(prev_trailer, inputs=[current_index_state, trailer_list_state],
#                    outputs=[video_box, current_index_state])
#     next_btn.click(next_trailer, inputs=[current_index_state, trailer_list_state],
#                    outputs=[video_box, current_index_state])
#     close_btn.click(close_trailers,
#                     outputs=[video_box, current_index_state, trailer_list_state, video_group, chat_col, video_col])

#     return [query_input, chatbot, query_btn, lc_memory_state, video_box, trailer_list_state, current_index_state]
