#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from .environment import (
    get_active_project,
    get_default_user_agent,
    get_gemini_keys,
    load_environment,
)

# 模块导入时立即加载 .env
load_environment()

__all__ = [
    "load_environment",
    "get_active_project",
    "get_gemini_keys",
    "get_default_user_agent",
]

