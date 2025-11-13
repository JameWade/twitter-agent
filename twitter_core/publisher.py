#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Optional


class PublishModule:
    def __init__(self) -> None:
        pass

    async def publish_tweet_directly(self, tweet_content: str, client=None) -> bool:
        """直接发布推文到Twitter（使用传入的客户端）"""
        try:
            if not client:
                print("❌ 没有可用的Twitter客户端")
                return False

            print("🚀 正在发布推文...")

            # 使用传入的客户端发推
            tweet_obj = await client.create_tweet(text=tweet_content)

            if tweet_obj:
                # 获取用户名
                try:
                    user = await client.user
                    screen_name = user.screen_name if hasattr(user, "screen_name") else "user"
                except Exception:  # noqa: BLE001
                    screen_name = "user"

                tweet_url = f"https://twitter.com/{screen_name}/status/{tweet_obj.id}"
                print(f"✅ 推文发布成功: {tweet_url}")

                # 记录到文件
                self.record_published_tweet(tweet_url, tweet_content)

                return True
            else:
                print("❌ 推文发布失败")
                return False

        except Exception as e:  # noqa: BLE001
            print(f"❌ 发布推文时出错: {e}")
            return False

    def record_published_tweet(
        self,
        tweet_url: str,
        content: str,
        record_file: str = "posted_tweets.txt",
    ) -> None:
        """记录已发布的推文"""
        try:
            # 只保存到tuiwen.txt
            with open("tuiwen.txt", "w", encoding="utf-8") as f:
                f.write(content)

            print("💾 推文内容已保存到 tuiwen.txt")

        except Exception as e:  # noqa: BLE001
            print(f"⚠️ 推文记录保存失败: {e}")

    async def publish_with_confirmation(self, tweet_content: str, client=None) -> bool:
        """直接发布推文，不保存文件"""
        print("\n📝 生成的推文内容:")
        print("=" * 50)
        print(tweet_content)
        print("=" * 50)
        print(f"字符数: {len(tweet_content)}/250")

        return await self.publish_tweet_directly(tweet_content, client)

    def get_tweet_statistics(self, content: str) -> dict:
        """获取推文统计信息"""
        return {
            "length": len(content),
            "words": len(content.split()),
            "hashtags": content.count("#"),
            "mentions": content.count("@"),
            "emojis": len([c for c in content if ord(c) > 127]),
            "urls": len(
                [word for word in content.split() if word.startswith(("http://", "https://"))]
            ),
            "is_valid_length": len(content) <= 250,
        }

