#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Set

from twitter_core import PublishModule, TwitterClientManager

from .translator import TranslatorModule


class TranslateTwitterAgent:
    """翻译Agent - 监控所有关注用户的推文，翻译成中文并发布"""

    STATE_FILE = Path("translated_tweets.txt")
    PROCESSED_TWEETS_FILE = Path("translate_processed_tweets.txt")

    def __init__(self) -> None:
        self.client_manager = TwitterClientManager()
        self.publish = PublishModule()
        self.translator = TranslatorModule()

        self.twitter_client = None
        self.processed_tweet_ids: Set[str] = set()
        self.is_running = False

    async def initialize(self) -> bool:
        """初始化Twitter客户端"""
        print("🔗 初始化 Twitter 客户端...")
        self.twitter_client = await self.client_manager.login_twitter_client()

        if not self.twitter_client:
            print("❌ Twitter 客户端初始化失败")
            return False

        self._load_processed_tweets()
        print("✅ Twitter 客户端初始化成功")
        return True

    def _load_processed_tweets(self) -> None:
        """加载已处理的推文ID列表"""
        try:
            if self.PROCESSED_TWEETS_FILE.exists():
                with open(self.PROCESSED_TWEETS_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        tweet_id = line.strip()
                        if tweet_id:
                            self.processed_tweet_ids.add(tweet_id)
            print(f"📂 加载了 {len(self.processed_tweet_ids)} 条已处理推文记录")
        except Exception as exc:  # noqa: BLE001
            print(f"⚠️ 读取处理记录失败: {exc}")

    def _save_processed_tweet(self, tweet_id: str) -> None:
        """保存已处理的推文ID"""
        try:
            self.processed_tweet_ids.add(tweet_id)
            with open(self.PROCESSED_TWEETS_FILE, "a", encoding="utf-8") as f:
                f.write(f"{tweet_id}\n")
        except Exception as exc:  # noqa: BLE001
            print(f"⚠️ 写入处理记录失败: {exc}")

    def _save_translation_record(self, tweet_data: Dict, translation: str) -> None:
        """保存翻译记录到文件"""
        try:
            from datetime import datetime

            with open(self.STATE_FILE, "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"\n{'=' * 60}\n")
                f.write(f"时间: {timestamp}\n")
                f.write(f"推文ID: {tweet_data['id']}\n")
                f.write(f"作者: @{tweet_data['author']} ({tweet_data['author_name']})\n")
                f.write(f"原文: {tweet_data['content']}\n")
                f.write(f"中文翻译: {translation}\n")
                f.write(f"{'=' * 60}\n")

            print("💾 翻译记录已保存")
        except Exception as exc:  # noqa: BLE001
            print(f"❌ 保存翻译记录失败: {exc}")

    async def _get_timeline_tweets(self, limit: int = 20) -> List[Dict]:
        """获取时间线推文（来自关注的所有用户）"""
        try:
            if not self.twitter_client:
                return []

            print(f"🔍 正在获取时间线推文，限制数量: {limit}")

            # 使用 get_latest_timeline 获取时间线
            try:
                tweets_data = await self.twitter_client.get_latest_timeline(count=limit)  # type: ignore[union-attr]
            except Exception:  # noqa: BLE001
                try:
                    tweets_data = await self.twitter_client.get_latest_timeline(limit=limit)  # type: ignore[union-attr]
                except Exception:  # noqa: BLE001
                    tweets_data = await self.twitter_client.get_latest_timeline()  # type: ignore[union-attr]

            tweets: List[Dict] = []

            if tweets_data:
                all_tweets = list(tweets_data)
                print(f"📝 API返回了 {len(all_tweets)} 条推文")

                tweet_list = all_tweets[:limit]

                for i, tweet in enumerate(tweet_list):
                    try:
                        if hasattr(tweet, "text") and tweet.text:
                            author_screen_name = "unknown"
                            author_name = "unknown"
                            if hasattr(tweet, "user") and tweet.user:
                                author_screen_name = getattr(tweet.user, "screen_name", "unknown")
                                author_name = getattr(tweet.user, "name", "unknown")

                            tweet_id = str(getattr(tweet, "id", str(i)))

                            tweet_info = {
                                "id": tweet_id,
                                "content": tweet.text,
                                "author": author_screen_name,
                                "author_name": author_name,
                                "created_at": getattr(tweet, "created_at", ""),
                                "tweet_obj": tweet,
                            }
                            tweets.append(tweet_info)

                    except Exception as exc:  # noqa: BLE001
                        print(f"❌ 解析第 {i+1} 条推文失败: {exc}")
                        continue

            print(f"✅ 最终解析成功 {len(tweets)} 条推文")
            return tweets

        except Exception as exc:  # noqa: BLE001
            print(f"❌ 获取时间线失败: {exc}")
            import traceback

            traceback.print_exc()
            return []

    def _should_translate_tweet(self, tweet_data: Dict) -> bool:
        """判断是否应该翻译这条推文"""
        content = tweet_data["content"]
        tweet_id = tweet_data["id"]

        # 已处理过，跳过
        if tweet_id in self.processed_tweet_ids:
            return False

        # 跳过空内容
        if not content or not content.strip():
            return False

        # 跳过纯转发（RT开头）
        if content.strip().upper().startswith("RT @"):
            return False

        # 跳过过长的推文（可能是文章链接）
        if len(content) > 500:
            return False

        # 跳过纯链接或广告内容
        spam_indicators = [
            "follow me",
            "check out my",
            "buy now",
            "limited time",
            "click here",
            "link in bio",
        ]
        content_lower = content.lower()
        if any(indicator in content_lower for indicator in spam_indicators):
            return False

        return True

    async def _process_tweet(self, tweet_data: Dict) -> bool:
        """处理单条推文：翻译并发布"""
        try:
            tweet_id = tweet_data["id"]
            original_text = tweet_data["content"]
            author = tweet_data["author"]

            print(f"\n{'=' * 60}")
            print(f"📝 处理推文 (ID: {tweet_id})")
            print(f"👤 作者: @{author}")
            print(f"📄 原文: {original_text[:100]}...")

            # 翻译推文
            print("🌐 正在翻译...")
            translation = await self.translator.translate_to_chinese(original_text, author)

            if not translation:
                print("❌ 翻译失败，跳过此推文")
                self._save_processed_tweet(tweet_id)
                return False

            print(f"✅ 翻译完成: {translation[:100]}...")

            # 发布翻译后的推文
            print("📢 正在发布翻译推文...")
            success = await self.publish.publish_with_confirmation(translation, self.twitter_client)

            if success:
                print("✅ 翻译推文发布成功！")
                self._save_translation_record(tweet_data, translation)
                self._save_processed_tweet(tweet_id)
                return True
            else:
                print("❌ 翻译推文发布失败")
                return False

        except Exception as exc:  # noqa: BLE001
            print(f"❌ 处理推文出错: {exc}")
            import traceback

            traceback.print_exc()
            return False

    async def run_as_twitter_user(self) -> None:
        """像真实Twitter用户一样运行"""
        if not self.twitter_client:
            print("❌ Twitter 客户端未初始化")
            return

        print("🚀 翻译Agent开始运行...")
        print("📱 监控所有关注用户的推文，翻译成中文并发布")
        print("🛑 按 Ctrl+C 停止运行")
        print("=" * 60)

        self.is_running = True

        try:
            while self.is_running:
                print(f"\n{'=' * 60}")
                print(f"🕐 {asyncio.get_event_loop().time()} - 检查时间线")
                print(f"{'=' * 60}")

                # 获取时间线推文
                tweets = await self._get_timeline_tweets(limit=20)
                print(f"📡 总共获取到 {len(tweets)} 条推文")

                # 筛选需要翻译的新推文
                new_tweets = []
                for tweet in tweets:
                    if self._should_translate_tweet(tweet):
                        new_tweets.append(tweet)

                print(f"📊 发现 {len(new_tweets)} 条新推文需要翻译")

                # 处理每条新推文
                if new_tweets:
                    for i, tweet in enumerate(new_tweets, 1):
                        print(f"\n处理第 {i}/{len(new_tweets)} 条推文:")
                        success = await self._process_tweet(tweet)

                        if success:
                            # 发布成功后等待一段时间，避免频率过高
                            wait_time = 60  # 等待1分钟
                            print(f"⏱️ 等待 {wait_time} 秒后处理下一条...")
                            await asyncio.sleep(wait_time)
                        else:
                            # 失败后也等待一下
                            await asyncio.sleep(10)

                else:
                    print("✨ 没有新推文需要翻译")

                # 清理过期的processed_tweet_ids（只保留最近1000条）
                if len(self.processed_tweet_ids) > 1000:
                    print("🧹 清理过期的推文记录...")
                    self.processed_tweet_ids = set(list(self.processed_tweet_ids)[-1000:])

                # 等待一段时间后继续检查
                wait_time = 300  # 5分钟
                print(f"\n😴 等待 {wait_time} 秒后继续监控...")
                await asyncio.sleep(wait_time)

        except asyncio.CancelledError:
            print("⚠️ 翻译任务已取消")
            raise
        except KeyboardInterrupt:
            print("\n⚠️ 收到停止信号，结束监控")
        except Exception as exc:  # noqa: BLE001
            print(f"❌ 翻译Agent运行失败: {exc}")
            import traceback

            traceback.print_exc()
        finally:
            self.is_running = False

    async def cleanup(self) -> None:
        """清理资源"""
        if self.twitter_client:
            await self.client_manager.close_client()
        print("🧹 翻译Agent 清理完成")
