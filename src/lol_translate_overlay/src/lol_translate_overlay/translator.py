from __future__ import annotations

import os
from abc import ABC, abstractmethod

from openai import OpenAI

from .config import AppConfig


class TranslationError(RuntimeError):
    pass


class Translator(ABC):
    @abstractmethod
    def to_chinese(self, text: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def chinese_to_game_english(self, text: str) -> str:
        raise NotImplementedError


class OpenAITranslator(Translator):
    def __init__(self, model: str) -> None:
        if not os.getenv("OPENAI_API_KEY"):
            raise TranslationError("缺少 OPENAI_API_KEY。请复制 .env.example 为 .env 后填入 API Key。")
        self.client = OpenAI()
        self.model = model

    def _translate(self, system_prompt: str, text: str) -> str:
        text = text.strip()
        if not text:
            return ""

        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
        )
        result = response.output_text.strip()
        if not result:
            raise TranslationError("翻译服务没有返回内容。")
        return result

    def to_chinese(self, text: str) -> str:
        return self._translate(
            "你是游戏聊天翻译器。把英文或德文 LOL 聊天内容翻译成简洁自然的中文。"
            "保留召唤师技能、英雄名、路线、计时、ping、缩写和辱骂降温后的大意。"
            "只输出译文，不解释。",
            text,
        )

    def chinese_to_game_english(self, text: str) -> str:
        return self._translate(
            "你是英雄联盟玩家聊天翻译器。把中文翻译成自然、简短、适合游戏内发送的英文。"
            "优先使用 LOL 玩家常用表达，语气清楚但不过度挑衅。"
            "只输出英文句子，不解释。",
            text,
        )


class DeepLTranslator(Translator):
    def __init__(self) -> None:
        raise TranslationError("DeepL 接口已预留，但当前版本还未启用。请先使用 OpenAI。")

    def to_chinese(self, text: str) -> str:
        raise NotImplementedError

    def chinese_to_game_english(self, text: str) -> str:
        raise NotImplementedError


def create_translator(config: AppConfig) -> Translator:
    if config.provider == "openai":
        return OpenAITranslator(config.openai_model)
    if config.provider == "deepl":
        return DeepLTranslator()
    raise TranslationError(f"未知翻译服务：{config.provider}")

