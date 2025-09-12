#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter客户端统一管理模块
提供统一的Twitter客户端初始化和账号管理功能
"""

import httpx
import sys
import os
from typing import Dict, Optional, Tuple

# 添加twikit路径
sys.path.append('./twikit-main')
from twikit import Client

class TwitterClientManager:
    """Twitter客户端管理器"""
    
    def __init__(self):
        self.client = None
    
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
    
    def load_twitter_client(self, cookies_file: str = 'cookies.txt') -> Optional[Client]:
        """加载Twitter客户端"""
        try:
            # 优先使用环境变量
            if os.getenv('TWITTER_COOKIE'):
                headers = {
                    'User-Agent': os.getenv('TWITTER_USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
                    'Authorization': os.getenv('TWITTER_AUTHORIZATION', '')
                }
                cookies_str = os.getenv('TWITTER_COOKIE', '')
                proxy = os.getenv('TWITTER_PROXY', '')
                
                cookies = {}
                if cookies_str:
                    for c in cookies_str.split(';'):
                        if '=' in c:
                            ck, cv = c.strip().split('=', 1)
                            cookies[ck] = cv
                
                if proxy and not proxy.startswith(("http://", "https://", "socks5://")):
                    proxy = "socks5://" + proxy
                
                client = Client()
                timeout = httpx.Timeout(10.0, connect=5.0)
                client.http = httpx.AsyncClient(proxy=proxy, headers=headers, cookies=cookies, timeout=timeout)
                
                self.client = client
                return client
            else:
                # 回退到文件方式
                with open(cookies_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                raw_accounts = content.strip().split('\n\n')
                if raw_accounts:
                    headers, cookies, proxy = self.parse_account_headers(raw_accounts[0])
                    
                    if proxy and not proxy.startswith(("http://", "https://", "socks5://")):
                        proxy = "socks5://" + proxy
                    
                    client = Client()
                    timeout = httpx.Timeout(10.0, connect=5.0)
                    client.http = httpx.AsyncClient(proxy=proxy, headers=headers, cookies=cookies, timeout=timeout)
                    
                    self.client = client
                    return client
        except Exception as e:
            print(f"❌ Twitter客户端加载失败: {e}")
        return None
    
    async def close_client(self):
        """关闭Twitter客户端"""
        if self.client and hasattr(self.client, 'http'):
            try:
                await self.client.http.aclose()
                print("🔒 Twitter客户端已关闭")
            except:
                pass
