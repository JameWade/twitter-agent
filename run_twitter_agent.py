#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter Agent 启动脚本
"""

import asyncio
import sys
import os

# 检查依赖
try:
    import httpx
    import google.generativeai as genai
    import bs4
except ImportError as e:
    print(f"❌ 缺少依赖: {e}")
    print("请运行: pip install -r requirements.txt")
    sys.exit(1)

from twitter_agent import TwitterAgent

async def main():
    """启动Twitter Agent主函数"""
    print("🤖 启动 Twitter Agent...")
    print("📱 模拟真实用户行为：发推、回复、互动")
    
    try:
        agent = TwitterAgent()
        
        # 初始化
        if not await agent.initialize():
            print("❌ 初始化失败，请检查cookies.txt配置")
            return
        
        # 像真实Twitter用户一样运行
        await agent.run_as_twitter_user()
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断运行")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'agent' in locals():
            await agent.cleanup()

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Twitter Agent - 智能推特机器人")
    print("=" * 60)
    print("🛑 提示: 按 Ctrl+C 可以随时停止程序")
    print("=" * 60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
