from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


APP_DIR = Path.home() / ".lol_translate_overlay"
CONFIG_PATH = APP_DIR / "config.json"


@dataclass(frozen=True)
class AppConfig:
    provider: str = "openai"
    openai_model: str = "gpt-4o-mini"
    deepl_target_lang: str = "ZH"
    auto_copy_english: bool = True
    auto_copy_clipboard_translation: bool = False
    hotkey_toggle: str = "ctrl+alt+t"
    hotkey_clipboard_to_chinese: str = "ctrl+alt+c"
    hotkey_chinese_to_english: str = "ctrl+alt+e"


def load_config() -> AppConfig:
    load_dotenv()

    data: dict[str, str] = {}
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            raw = json.load(f)
            if isinstance(raw, dict):
                data = {str(k): str(v) for k, v in raw.items()}

    return AppConfig(
        provider=data.get("provider", os.getenv("TRANSLATE_PROVIDER", "openai")).lower(),
        openai_model=data.get("openai_model", os.getenv("OPENAI_MODEL", "gpt-4o-mini")),
        deepl_target_lang=data.get("deepl_target_lang", "ZH"),
        auto_copy_english=_bool_value(data.get("auto_copy_english"), default=True),
        auto_copy_clipboard_translation=_bool_value(data.get("auto_copy_clipboard_translation"), default=False),
        hotkey_toggle=data.get("hotkey_toggle", "ctrl+alt+t"),
        hotkey_clipboard_to_chinese=data.get("hotkey_clipboard_to_chinese", "ctrl+alt+c"),
        hotkey_chinese_to_english=data.get("hotkey_chinese_to_english", "ctrl+alt+e"),
    )


def ensure_user_config_exists() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_PATH.exists():
        return

    defaults = AppConfig()
    CONFIG_PATH.write_text(
        json.dumps(defaults.__dict__, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _bool_value(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
