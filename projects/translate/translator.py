#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import time
from typing import List, Optional

try:
    import google.generativeai as genai
except ImportError:
    print("⚠️ 请安装 Google Generative AI: pip install google-generativeai")
    genai = None

from config import get_gemini_keys


class TranslatorModule:
    """负责将推文翻译成中文的模块"""

    def __init__(self) -> None:
        self.gemini_model = None
        self.gemini_pool: Optional[GeminiKeyPool] = None
        self._init_gemini()

    def _init_gemini(self) -> None:
        """初始化Gemini AI客户端"""
        try:
            keys: List[str] = get_gemini_keys()
            if not keys:
                fallback = os.getenv("GEMINI_API_KEY")
                if fallback:
                    keys = [fallback]

            if not keys:
                print("❌ 未配置 Gemini API Key（请在环境变量中设置 GEMINI_API_KEYS 或 GEMINI_API_KEY）")
                self.gemini_pool = None
                self.gemini_model = None
                return

            # 构建密钥轮询池
            self.gemini_pool = GeminiKeyPool(keys=keys, model_name="gemini-2.0-flash-001")
            # 预置一个客户端以验证可用性（不会固定住该 key）
            if genai and self.gemini_pool:
                _ = self.gemini_pool.get_model()
                self.gemini_model = _
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Gemini 初始化失败: {exc}")

    async def translate_to_chinese(self, tweet_text: str, author: str = "") -> Optional[str]:
        """将推文翻译成中文"""
        if not self.gemini_pool:
            print("❌ 未初始化 Gemini 模型，无法翻译")
            return None

        prompt = f"""请将以下英文推文翻译成中文。要求：
1. 准确传达原意，语言自然流畅
2. 保留原文的语气和风格
3. 如果推文包含技术术语或专有名词，使用常见的中文译名或保留原文
4. 长度控制在合理范围内（如果原文较长，可以适当概括）
5. 如果是中文推文，直接返回原文
6. 不要添加任何解释或说明文字，只输出翻译后的中文内容

推文内容：
{tweet_text}

中文翻译："""

        # 使用密钥池进行重试与轮询
        max_attempts = max(3, len(self.gemini_pool.keys) * 2)
        base_delay = 1.0
        
        import asyncio
        import random
        
        for attempt in range(1, max_attempts + 1):
            try:
                model = self.gemini_pool.get_model()
                if not model:
                    raise RuntimeError("Gemini 模型不可用（无可用密钥）")
                response = model.generate_content(prompt)
                text = getattr(response, "text", "") or ""
                translation = text.strip()
                
                # 清理格式符号
                translation = (
                    translation.replace('"', "")
                    .replace("'", "")
                    .replace("翻译：", "")
                    .replace("中文翻译：", "")
                    .strip()
                )
                
                return translation
            except Exception as exc:  # noqa: BLE001
                msg = str(exc)
                is_rate_limited = (
                    ("429" in msg) or ("ResourceExhausted" in msg) or ("rate limit" in msg.lower())
                )
                if is_rate_limited:
                    self.gemini_pool.backoff_current_key()
                    delay = base_delay * (2 ** min(attempt - 1, 4))
                    delay = delay + random.uniform(0, 0.5)
                    print(f"⏳ Gemini 触发限流，等待 {delay:.1f}s 后重试（第{attempt}/{max_attempts}次）")
                    await asyncio.sleep(delay)
                    continue
                else:
                    print(f"❌ AI翻译失败: {exc}")
                    return None
        print("❌ 多次尝试后仍失败（可能持续限流或网络问题）")
        return None


class GeminiKeyPool:
    """简单的Gemini API密钥池，支持轮询与指数退避。"""

    def __init__(self, keys: List[str], model_name: str, ban_seconds: int = 60):
        self.keys = [k for k in (keys or []) if k]
        self.model_name = model_name
        self.index = 0
        self.key_ban_until: dict[str, float] = {}
        self.ban_seconds = max(10, ban_seconds)

    def _is_key_available(self, key: str) -> bool:
        now = time.time()
        until = self.key_ban_until.get(key, 0)
        return now >= until

    def _next_available_key(self) -> str | None:
        if not self.keys:
            return None
        start = self.index
        for _ in range(len(self.keys)):
            key = self.keys[self.index]
            self.index = (self.index + 1) % len(self.keys)
            if self._is_key_available(key):
                return key
        # 如果都在ban期，返回最早解禁的那个
        earliest_key = min(self.keys, key=lambda k: self.key_ban_until.get(k, 0))
        return earliest_key

    def backoff_current_key(self) -> None:
        if not self.keys:
            return
        # 上一个使用的 key 是 index-1
        key = self.keys[(self.index - 1) % len(self.keys)]
        self.key_ban_until[key] = time.time() + self.ban_seconds

    def get_model(self):
        if not genai:
            return None
        key = self._next_available_key()
        if not key:
            return None
        genai.configure(api_key=key)
        return genai.GenerativeModel(self.model_name)
