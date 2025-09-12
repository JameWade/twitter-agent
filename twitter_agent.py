#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter Agent - 智能推特机器人
模拟真实用户使用Twitter的行为：发推、回复、互动
"""

import asyncio
import sys
import random
from datetime import datetime, timedelta
from typing import Optional

# 导入各个模块
from twitter_client import TwitterClientManager
from research_module import ResearchModule
from analysis_module import AnalysisModule
from publish_module import PublishModule
from timeline_monitor import TimelineMonitor

class TwitterAgent:
    """Twitter Agent - 模拟真实Twitter用户行为"""
    
    def __init__(self):
        self.client_manager = TwitterClientManager()
        self.research = ResearchModule()
        self.analysis = AnalysisModule()
        self.publish = PublishModule()
        self.timeline_monitor = TimelineMonitor()
        
        self.twitter_client = None
        self.is_running = False
        self.last_activity = datetime.now()
    
    async def initialize(self) -> bool:
        """初始化Twitter客户端"""
        print("🔗 初始化Twitter客户端...")
        self.twitter_client = self.client_manager.load_twitter_client()
        
        if not self.twitter_client:
            print("❌ Twitter客户端初始化失败")
            return False
        
        print("✅ Twitter客户端初始化成功")
        return True
    
    async def generate_research_tweet(self) -> str:
        """生成基于调研的推文"""
        try:
            print("🔍 开始调研Monad相关信息...")
            
            # 获取Twitter数据
            twitter_data = []
            if self.twitter_client:
                twitter_data = await self.research.search_twitter_monad(self.twitter_client)
            
            if twitter_data:
                tweet = await self.analysis.analyze_and_generate_simple_content(twitter_data, {})
                return tweet
            else:
                raise Exception("没有获取到数据，无法生成调研推文")
        except Exception as e:
            print(f"❌ 生成调研推文失败: {e}")
            return None
    
    
    async def publish_tweet(self, content: str) -> bool:
        """发布推文"""
        try:
            if not self.twitter_client:
                print("❌ Twitter客户端未初始化")
                return False
            
            success = await self.publish.publish_with_confirmation(content, self.twitter_client)
            return success
        except Exception as e:
            print(f"❌ 发布推文失败: {e}")
            return False
    
    async def post_research_tweet(self) -> bool:
        """发布一条调研推文"""
        try:
            print("🔍 正在调研Monad相关信息...")
            tweet = await self.generate_research_tweet()
            
            if tweet:
                success = await self.publish_tweet(tweet)
                if success:
                    print("✅ 调研推文发布成功！")
                    self.last_activity = datetime.now()
                    return True
                else:
                    print("❌ 调研推文发布失败")
                    return False
            else:
                print("❌ 调研推文生成失败")
                return False
        except Exception as e:
            print(f"❌ 发布调研推文出错: {e}")
            return False
    
    
    
    async def should_post_tweet(self) -> bool:
        """判断是否应该发推文"""
        # 距离上次活动的时间
        time_since_last_activity = datetime.now() - self.last_activity
        
        # 至少间隔1分钟才发推
        if time_since_last_activity.total_seconds() < 60:  # 1分钟
            return False
        
        # 随机决定是否发推（50%概率）
        return random.random() < 0.5
    
    
    async def cleanup(self):
        """清理资源"""
        if self.twitter_client:
            await self.client_manager.close_client()
        print("🧹 资源清理完成")
    
    async def run_as_twitter_user(self):
        """像真实Twitter用户一样运行"""
        print("🤖 Twitter Agent 开始运行...")
        print("📱 模拟真实用户行为：发推、回复、互动")
        print("🛑 按 Ctrl+C 停止运行")
        print("="*60)
        
        # 设置时间线监控器的客户端
        self.timeline_monitor.twitter_client = self.twitter_client
        
        try:
            # 创建两个并发任务
            import asyncio
            
            # 任务1：时间线监控（回复评论）
            timeline_task = asyncio.create_task(
                self.timeline_monitor.run(check_interval=180)
            )
            
            # 任务2：调研发推
            research_task = asyncio.create_task(
                self.run_research_loop()
            )
            
            # 同时运行两个任务
            await asyncio.gather(timeline_task, research_task, return_exceptions=True)
                
        except KeyboardInterrupt:
            print("\n⚠️ 收到停止信号，正在关闭...")
            # 取消所有任务
            timeline_task.cancel()
            research_task.cancel()
            print("✅ 所有任务已停止")
        except Exception as e:
            print(f"❌ 运行出错: {e}")
    
    async def run_research_loop(self):
        """调研发推循环"""
        try:
            while True:
                try:
                    # 检查是否应该发推
                    if await self.should_post_tweet():
                        print("📝 决定发一条推文...")
                        await self.post_research_tweet()
                    else:
                        print("🔍 决定不发推文...")
                    
                    # 等待一段时间再检查
                    wait_time = random.randint(600, 900)  # 1-3分钟
                    print(f"⏰ 调研发推等待 {wait_time} 秒...")
                    await asyncio.sleep(wait_time)
                    
                except Exception as e:
                    print(f"❌ 调研发推出错: {e}")
                    await asyncio.sleep(300)  # 出错后等待5分钟
        except KeyboardInterrupt:
            print("📝 调研发推任务已停止")
            raise

