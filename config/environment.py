#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv


def load_environment(env_path: Optional[str] = None, *, override: bool = False) -> None:
    """加载 .env 环境变量文件"""
    candidate_paths = []

    if env_path:
        candidate_paths.append(Path(env_path))

    # 默认加载项目根目录的 .env
    project_root = Path(__file__).resolve().parent.parent
    candidate_paths.append(project_root / ".env")

    for path in candidate_paths:
        if path.exists():
            load_dotenv(path, override=override)
            break
    else:
        # 即使没有找到文件，也加载默认环境（用于系统环境变量）
        load_dotenv(override=override)


@lru_cache()
def get_active_project() -> str:
    """获取当前激活的项目标识"""
    return os.getenv("ACTIVE_PROJECT", "monad").strip()


@lru_cache()
def get_gemini_keys() -> List[str]:
    """从环境变量中获取 Gemini API Key 列表"""
    raw = os.getenv("GEMINI_API_KEYS", "")
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    return keys


@lru_cache()
def get_default_user_agent() -> str:
    """获取默认的 User-Agent"""
    return os.getenv(
        "TWITTER_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    )

