#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Twitter Agent 入口模块。

该模块用于暴露当前激活的项目 Agent，便于启动脚本保持兼容。
如需切换不同项目，可通过环境变量 ACTIVE_PROJECT 控制。
"""

from __future__ import annotations

from config import get_active_project
from projects.monad import MonadTwitterAgent
from projects.translate import TranslateTwitterAgent
from projects.zama import ZamaTwitterAgent

PROJECT_REGISTRY = {
    "monad": MonadTwitterAgent,
    "zama": ZamaTwitterAgent,
    "translate": TranslateTwitterAgent,
}

active_project = get_active_project().lower()
TwitterAgent = PROJECT_REGISTRY.get(active_project, MonadTwitterAgent)

if TwitterAgent is MonadTwitterAgent and active_project not in PROJECT_REGISTRY:
    print(f"⚠️ 未找到项目 '{active_project}' ，已回退到 Monad 配置")

__all__ = ["TwitterAgent", "MonadTwitterAgent", "ZamaTwitterAgent", "TranslateTwitterAgent"]

