#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import httpx
import re
import sys
from bs4 import BeautifulSoup
from typing import Dict, List, Optional

# 添加twikit路径
sys.path.append('./twikit-main')
from twikit import Client

class ResearchModule:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
    async def search_twitter_monad(self, client: Client) -> List[Dict]:
        """搜索10条最新和10条热门Monad相关推文，全部返回"""
        all_tweets = []
        
        try:
            print("🔍 正在搜索Twitter上的Monad相关推文...")
            
            # 搜索最新推文
            print("\n🔥 搜索最新推文...")
            latest_results = await client.search_tweet('monad', 'Latest')
            
            if latest_results:
                print(f"✅ 搜索到 {len(latest_results)} 条最新推文，取前10条:")
                
                for i, tweet in enumerate(latest_results[:10]):
                    if tweet.text:
                        author = tweet.user.screen_name if tweet.user else 'unknown'
                        print(f"\n🔆 最新推文 {i+1}: @{author}")
                        print(f"   内容: {tweet.text}")
                        all_tweets.append({
                            'content': tweet.text,
                            'source': 'latest',
                            'author': author
                        })
            
            # 搜索热门推文
            print("\n\n🔥 搜索热门推文...")
            top_results = await client.search_tweet('monad', 'Top')
            
            if top_results:
                print(f"✅ 搜索到 {len(top_results)} 条热门推文，取前10条:")
                
                for i, tweet in enumerate(top_results[:10]):
                    if tweet.text:
                        author = tweet.user.screen_name if tweet.user else 'unknown'
                        print(f"\n🔥 热门推文 {i+1}: @{author}")
                        print(f"   内容: {tweet.text}")
                        all_tweets.append({
                            'content': tweet.text,
                            'source': 'top',
                            'author': author
                        })
            
            print(f"\n\n📊 总计收集到 {len(all_tweets)} 条推文，全部用于分析")
                        
        except Exception as e:
            print(f"Twitter搜索失败: {e}")
            
        return all_tweets
    
