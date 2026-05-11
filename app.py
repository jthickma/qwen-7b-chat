"""Gradio app for the Gemma GGUF chat Space."""

from __future__ import annotations

import base64
import gc
import mimetypes
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

import gradio as gr
from huggingface_hub import hf_hub_download

try:
    from llama_cpp import Llama
    from llama_cpp import llama_chat_format
except ImportError:  # pragma: no cover - handled in the UI at runtime
    Llama = None
    llama_chat_format = None


MODEL_REPO = "HauhauCS/Gemma-4-E4B-Uncensored-HauhauCS-Aggressive"
MODEL_FILE = "Gemma-4-E4B-Uncensored-HauhauCS-Aggressive-Q5_K_P.gguf"
MMPROJ_FILE = "mmproj-Gemma-4-E4B-Uncensored-HauhauCS-Aggressive-f16.gguf"

DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."
DEFAULT_MAX_TOKENS = 1024
DEFAULT_CONTEXT = 8192

CSS = """
.small-note {font-size: 0.85rem; opacity: 0.72;}
.disclaimer {font-size: 0.78rem; opacity: 0.75;}
"""

EXAMPLES = [
    ["Explain the plot of Cinderella in a sentence."],
    ["What are some common mistakes to avoid when writing code?"],
    ["Suggest four metaphors to describe the benefits of AI"],
    ["Write a pop song about leaving home for the sandy beaches."],
    ["How long does it take to become proficient in French?"],
]


@dataclass(frozen=True)
class GenerationConfig:
    """Generation settings shared by chat and API calls."""

    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1


def _image_to_data_url(image_path: str | None) -> str | None:
    if not image_path:
        return None

    path = Path(image_path)
    mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _download_model(filename: str) -> str:
    return hf_hub_download(repo_id=MODEL_REPO, filename=filename)


def _make_chat_handler(mmproj_path: str) -> Any | None:
    """Build a vision chat handler when llama-cpp-python provides one."""

    if llama_chat_format is None or not Path(mmproj_path).exists():
        return None

    for handler_name in (
        "Gemma3ChatHandler",
        "Llava15ChatHandler",
        "Llava16ChatHandler",
    ):
        handler = getattr(llama_chat_format, handler_name, None)
        if handler is not None:
            return handler(clip_model_path=mmproj_path)

    return None


@lru_cache(maxsize=1)
def get_llm() -> Any:
    """Load the GGUF model once per Space process."""

    if Llama is None:
        raise gr.Error(
            "llama-cpp-python is not installed. Install requirements.txt and "
            "restart the Space."
        )

    model_path = _download_model(MODEL_FILE)
    mmproj_path = _download_model(MMPROJ_FILE)
    chat_handler = _make_chat_handler(mmproj_path)

    gpu_layers = int(os.getenv("N_GPU_LAYERS", "99"))
    context_size = int(os.getenv("N_CTX", str(DEFAULT_CONTEXT)))
    threads = int(os.getenv("N_THREADS", str(os.cpu_count() or 2)))

    return Llama(
        model_path=model_path,
        chat_handler=chat_handler,
        n_ctx=context_size,
        n_gpu_layers=gpu_layers,
        n_threads=threads,
        verbose=False,
    )


def _build_messages(
    message: str,
    history: list[list[str | None]] | None,
    system_prompt: str,
    image_path: str | None = None,
) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    if system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt.strip()})

    for user_text, assistant_text in history or []:
        if user_text:
            messages.append({"role": "user", "content": user_text})
        if assistant_text:
            messages.append({"role": "assistant", "content": assistant_text})

    image_url = _image_to_data_url(image_path)
    if image_url:
        messages.append(
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": message},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        )
    else:
        messages.append({"role": "user", "content": message})

    return messages


def _completion_kwargs(config: GenerationConfig) -> dict[str, Any]:
    return {
        "max_tokens": int(config.max_tokens),
        "temperature": float(config.temperature),
        "top_p": float(config.top_p),
        "top_k": int(config.top_k),
        "repeat_penalty": float(config.repeat_penalty),
    }


def _stream_chat_completion(
    messages: list[dict[str, Any]],
    config: GenerationConfig,
) -> Iterable[str]:
    stream = get_llm().create_chat_completion(
        messages=messages,
        stream=True,
        **_completion_kwargs(config),
    )

    text = ""
    for chunk in stream:
        delta = chunk["choices"][0].get("delta", {})
        token = delta.get("content")
        if token:
            text += token
            yield text


def respond(
    message: str,
    image: str | None,
    history: list[list[str | None]] | None,
    system_prompt: str,
    max_tokens: int,
    temperature: float,
    top_p: float,
    top_k: int,
    repeat_penalty: float,
) -> Iterable[tuple[list[list[str | None]], str | None]]:
    """Generate a streaming chat response for the Gradio UI."""

    message = (message or "").strip()
    if not message and not image:
        yield history or [], image
        return

    if not message:
        message = "Describe this image."

    history = list(history or [])
    visible_message = message if not image else f"{message}\n\n[image attached]"
    history.append([visible_message, ""])

    config = GenerationConfig(
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        repeat_penalty=repeat_penalty,
    )
    messages = _build_messages(message, history[:-1], system_prompt, image)

    try:
        for partial in _stream_chat_completion(messages, config):
            history[-1][1] = partial
            yield history, None
    except Exception as exc:
        history[-1][1] = f"Error: {exc}"
        yield history, image
    finally:
        gc.collect()


def api(
    input_text: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = 0.7,
    repeat_penalty: float = 1.1,
    top_k: int = 40,
    top_p: float = 0.9,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    history: list[list[str | None]] | None = None,
) -> str:
    """Public Gradio API endpoint compatible with gradio_client."""

    input_text = (input_text or "").strip()
    if not input_text:
        return ""

    config = GenerationConfig(
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        repeat_penalty=repeat_penalty,
    )
    messages = _build_messages(input_text, history or [], system_prompt)
    response = get_llm().create_chat_completion(
        messages=messages,
        stream=False,
        **_completion_kwargs(config),
    )
    return response["choices"][0]["message"]["content"]


def clear_chat() -> tuple[list[list[str | None]], None, str]:
    return [], None, ""


theme = gr.themes.Soft(text_size="sm")

with gr.Blocks(theme=theme, title=MODEL_REPO, css=CSS) as demo:
    gr.Markdown(f"# {MODEL_REPO.split('/')[-1]}")
    gr.Markdown(
        "Chat with the same GGUF model used by the original llama.cpp Space.",
        elem_classes="small-note",
    )

    chatbot = gr.Chatbot(height=520)

    with gr.Row():
        with gr.Column(scale=5):
            msg = gr.Textbox(
                placeholder="Ask anything. Attach an image for vision prompts.",
                show_label=False,
                lines=4,
                max_lines=12,
            )
            image = gr.Image(label="Image", type="filepath")
        with gr.Column(scale=1, min_width=120):
            submit = gr.Button("Submit", variant="primary")
            stop = gr.Button("Stop")
            clear = gr.Button("Clear")

    with gr.Accordion("Advanced options", open=False):
        system_prompt = gr.Textbox(
            label="System prompt",
            value=DEFAULT_SYSTEM_PROMPT,
            lines=3,
        )
        max_tokens = gr.Slider(
            label="Max new tokens",
            minimum=1,
            maximum=38912,
            value=DEFAULT_MAX_TOKENS,
            step=1,
        )
        temperature = gr.Slider(
            label="Temperature",
            minimum=0.0,
            maximum=2.0,
            value=0.7,
            step=0.05,
        )
        top_p = gr.Slider(
            label="Top-p",
            minimum=0.05,
            maximum=1.0,
            value=0.9,
            step=0.05,
        )
        top_k = gr.Slider(
            label="Top-k",
            minimum=0,
            maximum=1000,
            value=40,
            step=1,
        )
        repeat_penalty = gr.Slider(
            label="Repeat penalty",
            minimum=0.1,
            maximum=4.0,
            value=1.1,
            step=0.05,
        )

    with gr.Accordion("Example inputs", open=False):
        gr.Examples(examples=EXAMPLES, inputs=[msg])

    with gr.Accordion("Disclaimer", open=False):
        gr.Markdown(
            "This model can produce factually incorrect, biased, unsafe, or "
            "offensive output. Do not rely on it as a source of truth.",
            elem_classes="disclaimer",
        )

    inputs = [
        msg,
        image,
        chatbot,
        system_prompt,
        max_tokens,
        temperature,
        top_p,
        top_k,
        repeat_penalty,
    ]

    submit_event = submit.click(
        respond,
        inputs=inputs,
        outputs=[chatbot, image],
        queue=True,
    ).then(lambda: "", outputs=msg)
    msg_event = msg.submit(
        respond,
        inputs=inputs,
        outputs=[chatbot, image],
        queue=True,
    ).then(lambda: "", outputs=msg)
    stop.click(
        fn=None,
        inputs=None,
        outputs=None,
        cancels=[submit_event, msg_event],
        queue=False,
    )
    clear.click(clear_chat, outputs=[chatbot, image, msg], queue=False)

    api_input = gr.Textbox(visible=False)
    api_history = gr.Chatbot(visible=False)
    api_output = gr.Textbox(visible=False)
    api_button = gr.Button(visible=False)
    api_button.click(
        api,
        [
            api_input,
            max_tokens,
            temperature,
            repeat_penalty,
            top_k,
            top_p,
            system_prompt,
            api_history,
        ],
        api_output,
        api_name="api",
    )


if __name__ == "__main__":
    demo.queue(max_size=8).launch()
