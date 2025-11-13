#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Optional

try:
    import google.generativeai as genai
except ImportError:
    print("⚠️ 请安装 Google Generative AI: pip install google-generativeai")
    genai = None


class ZamaContentModule:
    """负责为 Zama 项目生成中文互动内容与翻译推文"""

    def __init__(self) -> None:
        self.gemini_model = None
        self._init_gemini()

    def _init_gemini(self) -> None:
        try:
            import os

            api_key = os.getenv("GEMINI_API_KEY", "")
            if not api_key and os.getenv("GEMINI_API_KEYS"):
                api_key = os.getenv("GEMINI_API_KEYS").split(",")[0].strip()

            if api_key and genai:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel("gemini-2.0-flash-001")
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Gemini 初始化失败: {exc}")

    async def generate_comment(self, tweet_text: str) -> Optional[str]:
        """生成中文互动评论"""
        if not self.gemini_model:
            print("❌ 未初始化 Gemini 模型，无法生成评论")
            return None

        prompt = f"""你是一个中文 Twitter 用户，看到 @zama 的最新推文，需要用自然中文写一句评论。

推文内容：
{tweet_text}

要求：
1. 使用中文，语气自然友好，可以带少量 Emoji。
2. 控制在 30-60 字。
3. 表达个人观点或互动，不要重复原文。

直接输出评论内容："""

        return await self._call_gemini(prompt)

    async def generate_translation_post(self, tweet_text: str) -> Optional[str]:
        """根据 Zama 推文生成一条中文推文（翻译/解读）"""
        if not self.gemini_model:
            print("❌ 未初始化 Gemini 模型，无法生成翻译推文")
            return None

        prompt = f"""请你阅读下面这条英文推文，将其转述为一条正式的中文推文，面向中文 Web3 社区。

推文内容：
{tweet_text}

要求：
1. 用中文写 80-150 字，口吻专业清晰。
2. 概括重点信息，可以补充必要背景，但不要捏造事实。
3. 适当加入主题标签（例如 #Zama），最多 3 个。
4. 输出直接作为推文，勿加解释说明。

返回中文推文："""

        return await self._call_gemini(prompt)

    async def _call_gemini(self, prompt: str) -> Optional[str]:
        try:
            response = self.gemini_model.generate_content(prompt)
            text = getattr(response, "text", "") if response else ""
            return text.strip() or None
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Gemini 生成失败: {exc}")
            return None

