#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter客户端统一管理模块
提供统一的Twitter客户端初始化和账号管理功能
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
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

    async def login_twitter_client(self) -> Optional[Client]:
        """登录Twitter客户端（TWITTER_COOKIE和用户名密码都是必填）"""
        try:
            # 必填参数：从环境变量读取
            cookies_str = os.getenv("TWITTER_COOKIE", "")
            username = os.getenv("TWITTER_USERNAME", "")
            email = os.getenv("TWITTER_EMAIL", "")
            password = os.getenv("TWITTER_PASSWORD", "")
            proxy = os.getenv("TWITTER_PROXY", "") or None

            # 检查必填参数
            if not cookies_str:
                print("❌ TWITTER_COOKIE 是必填参数")
                return None
            if not (username or email) or not password:
                print("❌ TWITTER_USERNAME/TWITTER_EMAIL 和 TWITTER_PASSWORD 是必填参数")
                return None

            # 初始化客户端
            client = Client('en-US')
            
            # 设置代理（如果有）
            if proxy and not proxy.startswith(("http://", "https://", "socks5://")):
                proxy = "socks5://" + proxy
            
            if proxy:
                timeout = httpx.Timeout(10.0, connect=5.0)
                client.http = httpx.AsyncClient(proxy=proxy, timeout=timeout)
            
            # 解析cookie
            env_block_lines = [f"Cookie: {cookies_str}"]
            env_block = "\n".join(env_block_lines)
            headers, cookies, _ = self.parse_account_headers(env_block)
            
            # 将cookies转换为JSON并保存到临时文件
            cookies_json_file = None
            if cookies:
                # 将cookies字典转换为JSON格式
                cookies_json = json.dumps(cookies, indent=2)
                
                # 保存到临时文件
                with tempfile.NamedTemporaryFile(
                    mode='w', suffix='.json', delete=False, encoding='utf-8', dir='.'
                ) as tmp_file:
                    tmp_file.write(cookies_json)
                    cookies_json_file = tmp_file.name
                
                print(f"📝 Cookies已转换为JSON并保存到临时文件: {cookies_json_file}")
            
            # 登录（login方法会自动检查cookie是否有效，无效则用用户名密码登录）
            print("🔐 正在登录...")
            print(f"   用户名/邮箱: {username or email}")
            print(f"   代理: {proxy or '无'}")
            await client.login(
                auth_info_1=username or email,
                auth_info_2=email if username else None,
                password=password,
                cookies_file=cookies_json_file
            )
            
            self.client = client
            print("✅ Twitter 登录成功！")
            return client
        except Exception as e:  # noqa: BLE001
            import traceback
            error_msg = str(e)
            error_type = type(e).__name__
            print(f"\n{'=' * 60}")
            print(f"❌ Twitter 登录失败")
            print(f"{'=' * 60}")
            print(f"错误类型: {error_type}")
            print(f"错误信息: {error_msg}")
            print(f"\n详细错误堆栈:")
            traceback.print_exc()
            print(f"{'=' * 60}\n")
            return None

    async def close_client(self) -> None:
        """关闭Twitter客户端"""
        if self.client and hasattr(self.client, "http"):
            try:
                await self.client.http.aclose()
                print("🔒 Twitter客户端已关闭")
            except Exception:  # noqa: BLE001
                pass


