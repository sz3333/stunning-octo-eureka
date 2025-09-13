from .. import loader, utils
import aiohttp
import asyncio
import random
import string

@loader.tds
class MultiFemburnTGMod(loader.Module):
    """Мультипоиск и отправка артов e621 по тегам (без сохранения на диск)"""

    strings = {"name": "MultiFemburnTG"}

    def __init__(self):
        # Теги можно менять под себя
        self.tags = ["femboy", "catboy", "soft_male"]
        self.running = False

    async def multifemburncmd(self, message):
        """Запускает одновременную отправку артов по тегам"""
        if self.running:
            await message.edit("⚠️ Уже запущено!")
            return

        self.running = True
        await message.edit(f"🧦 Запущена отправка артов для тегов: {', '.join(self.tags)}")

        for tag in self.tags:
            asyncio.create_task(self._send_tag(message, tag))

    async def _send_tag(self, message, tag):
        headers = {"User-Agent": "HikkaBot/1.0 by Lidik"}

        while self.running:
            url = f"https://e621.net/posts.json?tags={tag}+order:random&limit=3"

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            await asyncio.sleep(60)
                            continue
                        data = await resp.json()
                        posts = data.get("posts", [])

                        for post in posts:
                            file_url = post.get("file", {}).get("url")
                            if not file_url:
                                continue

                            # Отправляем файл прямо в ТГ
                            try:
                                await message.client.send_file(
                                    message.chat_id,
                                    file_url,
                                    caption=f"🎨 Тег: {tag}"
                                )
                            except Exception:
                                continue

                            await asyncio.sleep(random.randint(10, 20))  # пауза между файлами

                except Exception:
                    await asyncio.sleep(30)

            await asyncio.sleep(random.randint(40, 90))  # пауза между раундами

    async def stopfemburncmd(self, message):
        """Остановить мультифембой"""
        self.running = False
        await message.edit("🛑 Отправка артов остановлена.")