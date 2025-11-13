#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter客户端统一管理模块
提供统一的Twitter客户端初始化和账号管理功能
"""

from __future__ import annotations

import os
import sys
from typing import Dict, Optional, Tuple

import httpx

# 添加 twikit 路径
sys.path.append("./twikit-main")
from twikit import Client  # noqa: E402

from config import get_default_user_agent


class TwitterClientManager:
    """Twitter客户端管理器"""

    def __init__(self) -> None:
        self.client: Optional[Client] = None
    
    def parse_account_headers(self, raw_text: str) -> Tuple[Dict, Dict, Optional[str]]:
        """解析账号头部信息"""
        headers = {}
        cookies_str = None
        proxy = None

        for line in raw_text.strip().splitlines():
            if not line.strip() or ':' not in line:
                continue
            key, val = line.split(':', 1)
            key = key.strip()
            val = val.strip()
            if key.lower() == 'cookie':
                cookies_str = val
            elif key.lower() == 'proxy':
                proxy = val
            else:
                headers[key] = val

        cookies = {}
        if cookies_str:
            for c in cookies_str.split(';'):
                if '=' in c:
                    ck, cv = c.strip().split('=', 1)
                    cookies[ck] = cv

        return headers, cookies, proxy

    def load_twitter_client(self) -> Optional[Client]:
        """加载Twitter客户端"""
        try:
            proxy = os.getenv("TWITTER_PROXY", "") or None
            cookies_str = os.getenv("TWITTER_COOKIE", "")

            if not cookies_str:
                print("❌ 缺少环境变量 TWITTER_COOKIE")
                return None

            # 构造一个与 cookies.txt 相同格式的块以复用解析逻辑
            env_block_lines = [
                f"Cookie: {cookies_str}",
            ]
            if proxy:
                env_block_lines.append(f"Proxy: {proxy}")
            env_block = "\n".join(env_block_lines)

            headers, cookies, proxy = self.parse_account_headers(env_block)

            if proxy and not proxy.startswith(("http://", "https://", "socks5://")):
                proxy = "socks5://" + proxy

            client = Client()
            timeout = httpx.Timeout(10.0, connect=5.0)
            client.http = httpx.AsyncClient(
                proxy=proxy,
                headers=headers,
                cookies=cookies,
                timeout=timeout,
            )

            self.client = client
            return client
        except Exception as e:  # noqa: BLE001
            print(f"❌ Twitter客户端加载失败: {e}")
        return None

    async def close_client(self) -> None:
        """关闭Twitter客户端"""
        if self.client and hasattr(self.client, "http"):
            try:
                await self.client.http.aclose()
                print("🔒 Twitter客户端已关闭")
            except Exception:  # noqa: BLE001
                pass


