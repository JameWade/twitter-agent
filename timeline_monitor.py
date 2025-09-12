#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Set
import json
import time

# 添加twikit路径
sys.path.append('./twikit-main')
from twikit import Client

try:
    import google.generativeai as genai
except ImportError:
    print("⚠️ 请安装 Google Generative AI: pip install google-generativeai")
    genai = None

class TimelineMonitor:
    def __init__(self):
        self.twitter_client = None
        self.gemini_client = None
        self.processed_tweets = set()  # 防止重复处理
        self.commented_tweets = set()  # 已评论的推文ID
        self.last_check_time = datetime.now()
        self._init_gemini()
        self._load_commented_tweets()
        
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
    
    def _load_commented_tweets(self):
        """加载已评论的推文ID列表"""
        try:
            with open('commented_tweets.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('推文ID:'):
                        tweet_id = line.replace('推文ID:', '').strip()
                        self.commented_tweets.add(tweet_id)
            print(f"📂 加载了 {len(self.commented_tweets)} 条已评论推文记录")
        except FileNotFoundError:
            print("📂 未找到评论记录文件，将创建新文件")
        except Exception as e:
            print(f"❌ 加载评论记录失败: {e}")
    
    def _save_comment_record(self, tweet_data: Dict, comment: str):
        """保存评论记录到文件"""
        try:
            with open('commented_tweets.txt', 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"\n{'='*60}\n")
                f.write(f"时间: {timestamp}\n")
                f.write(f"推文ID: {tweet_data['id']}\n")
                f.write(f"作者: @{tweet_data['author']} ({tweet_data['author_name']})\n")
                f.write(f"推文内容: {tweet_data['content']}\n")
                f.write(f"我的评论: {comment}\n")
                f.write(f"{'='*60}\n")
            
            # 添加到已评论集合
            self.commented_tweets.add(tweet_data['id'])
            print(f"💾 评论记录已保存")
            
        except Exception as e:
            print(f"❌ 保存评论记录失败: {e}")

    def _load_twitter_client(self):
        """加载Twitter客户端"""
        from twitter_client import TwitterClientManager
        manager = TwitterClientManager()
        return manager.load_twitter_client()

    async def get_timeline_tweets(self, limit: int = 10) -> List[Dict]:
        """获取时间线推文"""
        try:
            print(f"🔍 正在获取时间线推文，限制数量: {limit}")
            
            # 使用 get_latest_timeline 获取时间线
            # 尝试不同的参数名，如果都不行就手动截取
            try:
                tweets_data = await self.twitter_client.get_latest_timeline(count=limit)
            except:
                try:
                    tweets_data = await self.twitter_client.get_latest_timeline(limit=limit)
                except:
                    tweets_data = await self.twitter_client.get_latest_timeline()
            print(f"📡 获取到数据类型: {type(tweets_data)}")
            
            tweets = []
            
            if tweets_data:
                # twikit.utils.Result 是可迭代的，转换为列表
                all_tweets = list(tweets_data)
                print(f"📝 API返回了 {len(all_tweets)} 条推文")
                
                # 手动限制数量
                tweet_list = all_tweets[:limit]
                print(f"🔧 手动限制为 {len(tweet_list)} 条推文")
                
                for i, tweet in enumerate(tweet_list):
                    try:
                        # 确保tweet有必要的属性
                        if hasattr(tweet, 'text') and tweet.text:
                            # 获取作者信息
                            author_screen_name = 'unknown'
                            author_name = 'unknown'
                            if hasattr(tweet, 'user') and tweet.user:
                                author_screen_name = getattr(tweet.user, 'screen_name', 'unknown')
                                author_name = getattr(tweet.user, 'name', 'unknown')
                            
                            # 获取创建时间
                            tweet_time_str = getattr(tweet, 'created_at', '')
                            
                            tweet_id = getattr(tweet, 'id', str(i))
                            
                            tweet_info = {
                                'id': tweet_id,
                                'content': tweet.text,
                                'author': author_screen_name,
                                'author_name': author_name,
                                'created_at': tweet_time_str,
                                'tweet_obj': tweet
                            }
                            tweets.append(tweet_info)
                            
                    except Exception as e:
                        print(f"❌ 解析第 {i+1} 条推文失败: {e}")
                        continue
            else:
                print("❌ 没有获取到任何推文数据")
            
            print(f"✅ 最终解析成功 {len(tweets)} 条推文")
            return tweets
            
        except Exception as e:
            print(f"❌ 获取时间线失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def analyze_tweet_and_generate_comment(self, tweet_data: Dict) -> str:
        """分析推文并生成评论"""
        if not self.gemini_client:
            return None
            
        prompt = f"""看到这条推文，写一句话评论：

推文内容："{tweet_data['content']}"

要求：
1. 只写一句话
2. 30字以内
3. 自然回复即可

直接返回评论："""

        try:
            response = self.gemini_client.generate_content(prompt)
            comment = response.text.strip()
            
            # 清理格式符号
            comment = comment.replace('"', '').replace("'", '').replace('评论：', '').strip()
            
            # 确保是一句话，限制长度
            if len(comment) > 30:
                comment = comment[:30]
                
            return comment
            
        except Exception as e:
            print(f"❌ AI生成评论失败: {e}")
            return None

    async def post_comment(self, tweet_obj, comment_text: str) -> bool:
        """发布评论"""
        try:
            await tweet_obj.reply(comment_text)
            return True
        except Exception as e:
            print(f"❌ 发布评论失败: {e}")
            return False

    def should_comment_on_tweet(self, tweet_data: Dict) -> bool:
        """判断是否应该评论这条推文"""
        content = tweet_data['content'].lower()
        
        # 避免评论纯广告或垃圾内容
        spam_indicators = ['follow me', 'check out my', 'buy now', 'limited time', 'click here', 'link in bio']
        is_spam = any(indicator in content for indicator in spam_indicators)
        
        # 避免评论过长的推文（可能是文章）
        is_too_long = len(tweet_data['content']) > 500
        
        # 避免评论纯转发或引用推文
        is_retweet = content.startswith('rt @') or 'retweeted' in content
        
        # 避免评论自己的推文（如果有用户信息的话）
        is_own_tweet = False  # 这里可以根据需要添加逻辑
        
        # 只要不是垃圾内容、过长文章、转发内容，都评论
        return not is_spam and not is_too_long and not is_retweet and not is_own_tweet

    async def monitor_timeline(self, check_interval: int = 300):
        """监控时间线并自动评论"""
        print("🔍 开始监控时间线...")
        
        while True:
            try:
                print(f"\n{'='*60}")
                print(f"🕐 {datetime.now().strftime('%H:%M:%S')} - 检查时间线")
                print(f"{'='*60}")
                
                # 获取时间线推文
                tweets = await self.get_timeline_tweets(limit=10)
                print(f"📡 总共获取到 {len(tweets)} 条推文")
                
                # 显示所有推文（不管是否处理过）
                print(f"\n📋 当前时间线推文列表:")
                for i, tweet in enumerate(tweets, 1):
                    if tweet['id'] in self.commented_tweets:
                        status = "💬 已评论"
                    elif tweet['id'] in self.processed_tweets:
                        status = "📌 已处理"
                    else:
                        status = "🆕 新推文"
                    
                    print(f"{i:2d}. {status} @{tweet['author']:<15} | {tweet['content'][:80]}...")
                    print(f"    推文ID: {tweet['id']}")
                    print(f"    时间: {tweet.get('created_at', '未知')}")
                    print()
                
                # 筛选新推文
                new_tweets = []
                for tweet in tweets:
                    if tweet['id'] not in self.processed_tweets:
                        self.processed_tweets.add(tweet['id'])
                        new_tweets.append(tweet)
                
                print(f"📊 发现 {len(new_tweets)} 条新推文需要处理")
                
                # 处理每条新推文
                if new_tweets:
                    print(f"\n🔄 开始处理新推文:")
                    
                    # 随机选择部分推文进行评论，不要全部评论
                    import random
                    comment_count = min(2, len(new_tweets))  # 最多评论2条
                    tweets_to_comment = random.sample(new_tweets, comment_count) if len(new_tweets) >= comment_count else new_tweets
                    
                    print(f"🎯 从 {len(new_tweets)} 条新推文中随机选择 {len(tweets_to_comment)} 条进行评论")
                    
                    for i, tweet in enumerate(tweets_to_comment, 1):
                        print(f"\n处理第 {i}/{len(tweets_to_comment)} 条推文:")
                        print(f"👤 作者: @{tweet['author']}")
                        print(f"📝 内容: {tweet['content']}")
                        
                        # 检查是否已经评论过
                        if tweet['id'] in self.commented_tweets:
                            print(f"🔄 已评论过此推文，跳过")
                            continue
                            
                        if self.should_comment_on_tweet(tweet):
                            print(f"✅ 推文符合评论条件，开始生成评论...")
                            
                            # 30% 概率跳过评论，模拟真人不会每条都回复
                            if random.random() < 0.3:
                                print("🎲 随机跳过此推文（模拟真人行为）")
                                continue
                            
                            # 生成评论
                            comment = await self.analyze_tweet_and_generate_comment(tweet)
                            
                            if comment:
                                print(f"💬 生成的评论: {comment}")
                                
                                # 发布评论
                                success = await self.post_comment(tweet['tweet_obj'], comment)
                                
                                if success:
                                    print(f"✅ 评论发布成功!")
                                    # 保存评论记录
                                    self._save_comment_record(tweet, comment)
                                else:
                                    print(f"❌ 评论发布失败")
                                
                                # 随机休息30-90秒，模拟真人行为
                                rest_time = random.randint(30, 90)
                                print(f"⏱️ 休息 {rest_time} 秒...")
                                await asyncio.sleep(rest_time)
                            else:
                                print("❌ AI评论生成失败")
                        else:
                            print(f"⏭️ 跳过此推文 (不符合评论条件)")
                else:
                    print("✨ 没有新推文需要处理")
                
                # 清理过期的processed_tweets（只保留最近1000条）
                if len(self.processed_tweets) > 1000:
                    print("🧹 清理过期的推文记录...")
                    self.processed_tweets.clear()
                
                print(f"\n😴 等待 {check_interval} 秒后继续监控...")
                print(f"⏰ 下次检查时间: {(datetime.now() + timedelta(seconds=check_interval)).strftime('%H:%M:%S')}")
                await asyncio.sleep(check_interval)
                
            except KeyboardInterrupt:
                print("\n⚠️ 收到中断信号，正在停止监控...")
                break
            except Exception as e:
                print(f"❌ 监控过程出错: {e}")
                print("⏱️ 等待60秒后重试...")
                await asyncio.sleep(60)  # 出错后等待1分钟

    async def run(self, check_interval: int = 300):
        """启动时间线监控"""
        print("🚀 启动时间线监控系统...")
        
        # 初始化Twitter客户端
        self.twitter_client = self._load_twitter_client()
        
        if not self.twitter_client:
            print("❌ Twitter客户端初始化失败")
            return
            
        if not self.gemini_client:
            print("❌ Gemini AI未初始化")
            return
        
        print("✅ 系统初始化完成")
        print(f"⏰ 检查间隔: {check_interval} 秒")
        print("💬 会评论所有推文（过滤垃圾内容）")
        print("🛑 按 Ctrl+C 可以停止监控")
        
        try:
            await self.monitor_timeline(check_interval)
        except KeyboardInterrupt:
            print("\n⚠️ 用户中断监控")
        except Exception as e:
            print(f"❌ 系统运行失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 关闭Twitter客户端
            if self.twitter_client and hasattr(self.twitter_client, 'http'):
                try:
                    await self.twitter_client.http.aclose()
                    print("🔒 Twitter客户端已关闭")
                except:
                    pass
            print("👋 时间线监控已停止")

async def main():
    try:
        monitor = TimelineMonitor()
        await monitor.run(check_interval=180)  # 每3分钟检查一次
    except KeyboardInterrupt:
        print("\n👋 程序已停止")
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 Twitter时间线监控与AI评论系统")
    print("=" * 60)
    print("🛑 提示: 按 Ctrl+C 可以随时停止程序")
    print("=" * 60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 程序已退出")