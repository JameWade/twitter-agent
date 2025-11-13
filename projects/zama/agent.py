#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from twitter_core import PublishModule, TwitterClientManager

from .content import ZamaContentModule


class ZamaTwitterAgent:
    """追踪 @zama 推文并进行互动与转发的 Agent"""

    TARGET_SCREEN_NAME = "zama"
    STATE_FILE = Path("zama_last_tweet.txt")

    def __init__(self) -> None:
        self.client_manager = TwitterClientManager()
        self.publish = PublishModule()
        self.content = ZamaContentModule()

        self.twitter_client = None
        self.last_tweet_id: Optional[str] = None
        self.is_running = False

    async def initialize(self) -> bool:
        print("🔗 初始化 Twitter 客户端...")
        self.twitter_client = self.client_manager.load_twitter_client()

        if not self.twitter_client:
            print("❌ Twitter 客户端初始化失败")
            return False

        self.last_tweet_id = self._load_last_tweet_id()
        print("✅ Twitter 客户端初始化成功")
        return True

    def _load_last_tweet_id(self) -> Optional[str]:
        try:
            if self.STATE_FILE.exists():
                return self.STATE_FILE.read_text(encoding="utf-8").strip() or None
        except Exception as exc:  # noqa: BLE001
            print(f"⚠️ 读取状态文件失败: {exc}")
        return None

    def _save_last_tweet_id(self, tweet_id: str) -> None:
        try:
            self.STATE_FILE.write_text(tweet_id, encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            print(f"⚠️ 写入状态文件失败: {exc}")

    async def _fetch_latest_zama_tweet(self):
        """通过搜索接口获取 @zama 最新推文"""
        try:
            query = f"from:{self.TARGET_SCREEN_NAME}"
            results = await self.twitter_client.search_tweet(query, "Latest")
            if not results:
                return None

            for tweet in results:
                user = getattr(tweet, "user", None)
                screen_name = getattr(user, "screen_name", "").lower() if user else ""
                if screen_name == self.TARGET_SCREEN_NAME.lower():
                    return tweet
        except Exception as exc:  # noqa: BLE001
            print(f"❌ 获取 Zama 推文失败: {exc}")
        return None

    async def _like_tweet(self, tweet) -> bool:
        for attr in ("like", "favorite"):
            action = getattr(tweet, attr, None)
            if callable(action):
                try:
                    await action()
                    print("❤️ 已点赞该推文")
                    return True
                except Exception as exc:  # noqa: BLE001
                    print(f"⚠️ 点赞失败（方法 {attr}）: {exc}")
        print("⚠️ 未能点赞该推文")
        return False

    async def _retweet(self, tweet) -> bool:
        for attr in ("retweet", "repost"):
            action = getattr(tweet, attr, None)
            if callable(action):
                try:
                    await action()
                    print("🔁 已转发该推文")
                    return True
                except Exception as exc:  # noqa: BLE001
                    print(f"⚠️ 转发失败（方法 {attr}）: {exc}")
        print("⚠️ 未能转发该推文")
        return False

    async def _reply_in_chinese(self, tweet, original_text: str) -> None:
        comment = await self.content.generate_comment(original_text)
        if not comment:
            print("⚠️ 未生成评论，跳过回复")
            return

        reply_action = getattr(tweet, "reply", None)
        if not callable(reply_action):
            print("⚠️ 推文对象不支持回复")
            return

        try:
            await reply_action(comment)
            print(f"💬 已回复: {comment}")
        except Exception as exc:  # noqa: BLE001
            print(f"❌ 回复推文失败: {exc}")

    async def _publish_translation(self, original_text: str) -> None:
        translation = await self.content.generate_translation_post(original_text)
        if not translation:
            print("⚠️ 未生成翻译推文，跳过发布")
            return

        success = await self.publish.publish_with_confirmation(translation, self.twitter_client)
        if success:
            print("📢 翻译推文已发布")

    async def _process_new_tweet(self, tweet) -> None:
        tweet_id = getattr(tweet, "id", None)
        tweet_text = getattr(tweet, "text", "")
        if not tweet_id or not tweet_text:
            print("⚠️ 推文缺少必要信息，跳过")
            return

        if tweet_id == self.last_tweet_id:
            print("ℹ️ 没有新的 Zama 推文")
            return

        print(f"✨ 发现新推文 (ID: {tweet_id})，开始处理...")

        await self._like_tweet(tweet)
        await self._retweet(tweet)
        await self._reply_in_chinese(tweet, tweet_text)
        await self._publish_translation(tweet_text)

        self._save_last_tweet_id(str(tweet_id))
        self.last_tweet_id = str(tweet_id)
        print("✅ 推文处理完成")

    async def run_as_twitter_user(self) -> None:
        if not self.twitter_client:
            print("❌ Twitter 客户端未初始化")
            return

        print("🚀 开始追踪 @zama 的最新推文...")
        self.is_running = True

        try:
            while self.is_running:
                tweet = await self._fetch_latest_zama_tweet()
                if tweet:
                    await self._process_new_tweet(tweet)

                await asyncio.sleep(180)  # 每 3 分钟检查一次
        except asyncio.CancelledError:
            print("⚠️ Zama 追踪任务已取消")
            raise
        except KeyboardInterrupt:
            print("\n⚠️ 收到停止信号，结束追踪")
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Zama 追踪运行失败: {exc}")
        finally:
            self.is_running = False

    async def cleanup(self) -> None:
        if self.twitter_client:
            await self.client_manager.close_client()
        print("🧹 Zama Agent 清理完成")

