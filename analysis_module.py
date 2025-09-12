#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
from typing import Dict, List
from datetime import datetime

try:
    import google.generativeai as genai
except ImportError:
    print("⚠️ 请安装 Google Generative AI: pip install google-generativeai")
    genai = None

class AnalysisModule:
    def __init__(self):
        self.gemini_client = None
        self._init_gemini()
    
    def _init_gemini(self):
        """初始化Gemini AI客户端"""
        try:
            import os
            api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyCYHGwUsXFf7ZTF7q76r2oPyfXSR29elp4')
            
            if genai:
                genai.configure(api_key=api_key)
                self.gemini_client = genai.GenerativeModel('gemini-2.0-flash-001')
        except Exception as e:
            print(f"❌ Gemini AI 初始化失败: {e}")
    
    def choose_tweet_type(self) -> str:
        """选择推文类型：简单或深度分析"""
        current_hour = datetime.now().hour
        if 6 <= current_hour <= 10:
            return 'simple' if random.random() < 0.7 else 'research'
        return 'research' if random.random() < 0.6 else 'simple'
    
    async def analyze_and_generate_simple_content(self, twitter_data: List[Dict], testnet_data: Dict) -> str:
        """使用Gemini AI学习推文风格并生成150字左右的推文"""
        if not self.gemini_client:
            raise Exception("Gemini AI未初始化")
        if not twitter_data:
            raise Exception("没有Twitter数据")
        
        prompt = self._build_style_learning_prompt(twitter_data, testnet_data)
        response = await self._call_gemini(prompt)
        
        if not response:
            raise Exception("AI生成失败")
        
        tweet = self.validate_tweet_length(response, 150)
        return tweet
    
    def _build_style_learning_prompt(self, twitter_data: List[Dict], testnet_data: Dict) -> str:
        """构建风格学习提示词"""
        latest_tweets = [t['content'] for t in twitter_data if t['source'] == 'latest'][:5]
        top_tweets = [t['content'] for t in twitter_data if t['source'] == 'top'][:5]
        
        return f"""我是个关注Monad生态的Web3玩家，经常分享一些个人观察。

我现在为你搜集了最新的monad相关推文，我需要你参考这些推文内容，分析总结这些信息，做出总结或评论，写一条150字以内的原创推文：

{"\n".join([f"• {tweet}" for tweet in (latest_tweets + top_tweets)[:8]])}

要求：
1. 用第一人称，像个真人在发推，不要官方腔调
2. 可以表达个人看法
3. 语言要自然
4. 150字以内，可以包含emoji
5. 可以调侃、感叹或表达个人体验


直接返回推文内容："""
    
    async def _call_gemini(self, prompt: str) -> str:
        """调用Gemini AI生成内容"""
        try:
            response = self.gemini_client.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"❌ Gemini API 调用失败: {e}")
            return None
    
    async def synthesize_research_content(self, all_data: Dict) -> str:
        """使用Gemini AI进行深度分析并生成研究型推文"""
        if not self.gemini_client:
            raise Exception("Gemini AI未初始化")
        
        prompt = self._build_research_prompt(all_data)
        response = await self._call_gemini(prompt)
        
        if not response:
            raise Exception("深度分析AI失败")
        
        tweet = self.validate_tweet_length(response, 250)
        return tweet
    
    def _build_research_prompt(self, all_data: Dict) -> str:
        """构建深度研究提示词"""
        twitter_data = all_data.get('twitter', [])
        testnet_data = all_data.get('testnet', {})
        ecosystem_data = all_data.get('ecosystem', {})
        
        latest_count = len([t for t in twitter_data if t['source'] == 'latest'])
        top_count = len([t for t in twitter_data if t['source'] == 'top'])
        
        all_content = ' '.join([tweet['content'].lower() for tweet in twitter_data])
        keyword_stats = {
            'testnet': all_content.count('testnet') + all_content.count('devnet'),
            'mainnet': all_content.count('mainnet') + all_content.count('launch'),
            'parallel': all_content.count('parallel') + all_content.count('performance'),
            'funding': all_content.count('funding') + all_content.count('investment'),
            'ecosystem': all_content.count('ecosystem') + all_content.count('dapp')
        }
        
        return f"""我是个资深Web3玩家，经常深度分析项目。

基于以下Monad的真实数据，写一条200-250字的深度分析推文：

数据概况：
- Twitter讨论：最新{latest_count}条 + 热门{top_count}条
- 热门话题：{keyword_stats}
- 测试网状态：{testnet_data.get('status', '未知')}

部分推文内容：
{"\n".join([f"• {tweet['content'][:80]}..." for tweet in twitter_data[:3]])}

要求：
1. 用第一人称分析，像个人见解而非官方报告
2. 基于真实数据得出具体观点，不要泛泛而谈
3. 重点关注最热门的话题
4. 结合Monad的并行执行+EVM兼容优势
5. 语言要专业但不失人味，包含emoji
6. 200-250字，可以稍微犀利一点
7. 避免"赋能"、"生态建设"等官话套话

直接返回推文内容："""
    
    def validate_tweet_length(self, tweet: str, max_length: int = 250) -> str:
        """验证并调整推文长度"""
        if len(tweet) > max_length:
            return tweet[:max_length-3] + "..."
        return tweet
    
    def calculate_character_count(self, tweet: str) -> Dict:
        """计算字符数统计信息"""
        return {
            'total': len(tweet),
            'chinese': len([c for c in tweet if '\u4e00' <= c <= '\u9fff']),
            'english': len([c for c in tweet if c.isascii() and c.isalpha()]),
            'symbols': len([c for c in tweet if not c.isalnum() and not c.isspace()]),
            'spaces': tweet.count(' ')
        }