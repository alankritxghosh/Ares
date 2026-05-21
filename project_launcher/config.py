from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from project_launcher.catalog import DEFAULT_PROJECT_TYPE, DEFAULT_STAGE, PROJECT_TYPES


CONFIG_FILE = "ares.yaml"


@dataclass(frozen=True)
class AresConfig:
    name: str
    idea: str
    project_type: str = DEFAULT_PROJECT_TYPE
    stage: str = DEFAULT_STAGE
    primary_user: str = "To confirm"
    review_mode: str = "fast"
    quality_threshold: float = 9.5
    enabled_modules: list[str] | None = None

    @property
    def modules(self) -> list[str]:
        return self.enabled_modules or ["workspace", "knowledge", "health", "rag", "multiagent", "data"]


def default_config(name: str, idea: str, project_type: str = DEFAULT_PROJECT_TYPE, stage: str = DEFAULT_STAGE) -> AresConfig:
    if project_type not in PROJECT_TYPES:
        raise ValueError(f"Unknown project type: {project_type}. Run `ares catalog` to see available types.")
    return AresConfig(name=name, idea=idea, project_type=project_type, stage=stage)


def config_path(folder: Path) -> Path:
    return folder / CONFIG_FILE


def write_config(folder: Path, config: AresConfig) -> Path:
    path = config_path(folder)
    path.write_text(format_config(config), encoding="utf-8")
    return path


def load_config(folder: Path, fallback_name: str = "Unknown Project", fallback_idea: str = "") -> AresConfig:
    path = config_path(folder)
    if not path.is_file():
        return AresConfig(name=fallback_name, idea=fallback_idea)
    data = _parse_simple_yaml(path.read_text(encoding="utf-8"))
    modules = data.get("enabled_modules", [])
    if isinstance(modules, str):
        modules = [modules]
    return AresConfig(
        name=str(data.get("name", fallback_name)),
        idea=str(data.get("idea", fallback_idea)),
        project_type=str(data.get("type", data.get("project_type", DEFAULT_PROJECT_TYPE))),
        stage=str(data.get("stage", DEFAULT_STAGE)),
        primary_user=str(data.get("primary_user", "To confirm")),
        review_mode=str(data.get("review_mode", "fast")),
        quality_threshold=float(data.get("quality_threshold", 9.5)),
        enabled_modules=list(modules),
    )


def format_config(config: AresConfig) -> str:
    lines = [
        f'name: "{_escape(config.name)}"',
        f'idea: "{_escape(config.idea)}"',
        f"type: {config.project_type}",
        f"stage: {config.stage}",
        f'primary_user: "{_escape(config.primary_user)}"',
        f"review_mode: {config.review_mode}",
        f"quality_threshold: {config.quality_threshold:g}",
        "enabled_modules:",
    ]
    lines.extend(f"  - {module}" for module in config.modules)
    return "\n".join(lines).rstrip() + "\n"


def _parse_simple_yaml(text: str) -> dict[str, object]:
    data: dict[str, object] = {}
    current_list: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if current_list and line.startswith("  - "):
            data.setdefault(current_list, [])
            value = _parse_scalar(line[4:].strip())
            current = data[current_list]
            if isinstance(current, list):
                current.append(value)
            continue
        current_list = None
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not value:
            data[key] = []
            current_list = key
        else:
            data[key] = _parse_scalar(value)
    return data


def _parse_scalar(value: str) -> object:
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1].replace('\\"', '"')
    if value.replace(".", "", 1).isdigit():
        return float(value) if "." in value else int(value)
    return value


def _escape(value: str) -> str:
    return value.replace('"', '\\"')

