from __future__ import annotations

import base64
import json
import shutil
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


OLLAMA_HOST = "http://127.0.0.1:11434"
DEFAULT_CHAT_MODEL = "llama3.2"
BACKUP_CHAT_MODEL = "qwen2.5"
DEFAULT_EMBED_MODEL = "nomic-embed-text"
DEFAULT_VISION_MODEL = "moondream"
OPTIONAL_VISION_MODEL = "llava:7b"
REQUIRED_MODELS = [DEFAULT_CHAT_MODEL, BACKUP_CHAT_MODEL, DEFAULT_EMBED_MODEL, DEFAULT_VISION_MODEL]
SETUP_COMMANDS = [
    "ollama pull llama3.2",
    "ollama pull qwen2.5:3b-instruct",
    "ollama pull nomic-embed-text",
    "ollama pull moondream",
]


class LocalModelUnavailableError(ValueError):
    pass


@dataclass(frozen=True)
class ModelStatus:
    ollama_installed: bool
    ollama_path: str | None
    server_reachable: bool
    available_models: list[str]
    missing_models: list[str]
    setup_commands: list[str]
    error: str | None = None

    @property
    def ready_for_chat(self) -> bool:
        return self.server_reachable and _model_available(DEFAULT_CHAT_MODEL, self.available_models)

    @property
    def ready_for_embeddings(self) -> bool:
        return self.server_reachable and _model_available(DEFAULT_EMBED_MODEL, self.available_models)


def check_model_status(timeout: float = 2.0) -> ModelStatus:
    ollama_path = shutil.which("ollama")
    if not ollama_path:
        return ModelStatus(
            ollama_installed=False,
            ollama_path=None,
            server_reachable=False,
            available_models=[],
            missing_models=REQUIRED_MODELS,
            setup_commands=SETUP_COMMANDS,
            error="Ollama is not installed or not on PATH.",
        )

    try:
        payload = _request_json("GET", f"{OLLAMA_HOST}/api/tags", timeout=timeout)
    except LocalModelUnavailableError as exc:
        return ModelStatus(
            ollama_installed=True,
            ollama_path=ollama_path,
            server_reachable=False,
            available_models=[],
            missing_models=REQUIRED_MODELS,
            setup_commands=SETUP_COMMANDS,
            error=str(exc),
        )

    models = sorted(model.get("name", "") for model in payload.get("models", []) if model.get("name"))
    missing = [model for model in REQUIRED_MODELS if not _model_available(model, models)]
    return ModelStatus(
        ollama_installed=True,
        ollama_path=ollama_path,
        server_reachable=True,
        available_models=models,
        missing_models=missing,
        setup_commands=SETUP_COMMANDS,
    )


def format_model_status(status: ModelStatus) -> str:
    lines = [
        "Local Model Status",
        "",
        f"Ollama installed: {'yes' if status.ollama_installed else 'no'}",
        f"Ollama path: {status.ollama_path or 'not found'}",
        f"Ollama server reachable: {'yes' if status.server_reachable else 'no'}",
        "",
        "Available models:",
        *_bullets(status.available_models),
        "",
        "Missing recommended models:",
        *_bullets(status.missing_models),
    ]
    if status.error:
        lines.extend(["", f"Status note: {status.error}"])
    if status.missing_models or not status.server_reachable:
        lines.extend(["", "Setup commands:", *status.setup_commands])
    return "\n".join(lines).rstrip() + "\n"


def generate_text(prompt: str, model: str = DEFAULT_CHAT_MODEL, timeout: float = 60.0) -> str:
    _require_model(model, timeout=min(timeout, 5.0))
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2},
    }
    response = _request_json("POST", f"{OLLAMA_HOST}/api/generate", payload=payload, timeout=timeout)
    text = str(response.get("response", "")).strip()
    if not text:
        raise LocalModelUnavailableError("Local model returned an empty response.")
    return text


def describe_image(image_path: str, prompt: str, model: str = DEFAULT_VISION_MODEL, timeout: float = 60.0) -> str:
    _require_model(model, timeout=min(timeout, 5.0))
    image_bytes = base64.b64encode(open(image_path, "rb").read()).decode("ascii")
    payload = {
        "model": model,
        "prompt": prompt,
        "images": [image_bytes],
        "stream": False,
        "options": {"temperature": 0.1},
    }
    response = _request_json("POST", f"{OLLAMA_HOST}/api/generate", payload=payload, timeout=timeout)
    text = str(response.get("response", "")).strip()
    if not text:
        raise LocalModelUnavailableError("Local vision model returned an empty response.")
    return text


def embed_text(text: str, model: str = DEFAULT_EMBED_MODEL, timeout: float = 30.0) -> list[float]:
    _require_model(model, timeout=min(timeout, 5.0))
    payload = {"model": model, "prompt": text}
    response = _request_json("POST", f"{OLLAMA_HOST}/api/embeddings", payload=payload, timeout=timeout)
    embedding = response.get("embedding")
    if not isinstance(embedding, list):
        raise LocalModelUnavailableError("Local embedding model returned no embedding.")
    return [float(value) for value in embedding]


def setup_message() -> str:
    return (
        "Local models are not ready yet.\n\n"
        "Start Ollama locally, then run:\n"
        + "\n".join(SETUP_COMMANDS)
    )


def _require_model(model: str, timeout: float) -> None:
    status = check_model_status(timeout=timeout)
    if not status.server_reachable:
        raise LocalModelUnavailableError(setup_message())
    if not _model_available(model, status.available_models):
        raise LocalModelUnavailableError(setup_message())


def _request_json(method: str, url: str, payload: dict[str, Any] | None = None, timeout: float = 5.0) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise LocalModelUnavailableError(f"Could not reach local Ollama at {OLLAMA_HOST}.") from exc


def _model_available(model: str, models: list[str]) -> bool:
    requested = model.split(":", 1)[0]
    return any(candidate == model or candidate.split(":", 1)[0] == requested for candidate in models)


def _bullets(items: list[str]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]
