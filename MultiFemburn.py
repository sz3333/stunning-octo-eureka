from .. import loader
import aiohttp
import asyncio
import os
import random
import string
import datetime

@loader.tds
class MultiFemburnMod(loader.Module):
    """Мультифлудер по e621 тегам (SSD-у плохо, но красиво!)"""

    strings = {"name": "MultiFemburn"}

    def __init__(self):
        self.tags = ["femboy", "catboy", "soft_male"]  # Можешь редактировать теги по вкусу
        self.base_path = "/Heroku/heroku/e621_art"
        self.running = False

    async def multifemburncmd(self, message):
        """Запускает одновременную закачку артов по нескольким тегам"""
        if self.running:
            await message.edit("⚠️ Уже запущено!")
            return

        self.running = True
        await message.edit(f"🧦 Мультифембой-флуд запущен для: {', '.join(self.tags)}")

        for tag in self.tags:
            asyncio.create_task(self._flood_tag(tag))

    async def _flood_tag(self, tag):
        headers = {"User-Agent": "HikkaBot/1.0 by Lidik"}

        while self.running:
            now = datetime.datetime.now().strftime("%Y-%m-%d")
            folder = os.path.join(self.base_path, tag, now)
            os.makedirs(folder, exist_ok=True)
            open(os.path.join(folder, ".hidden"), "a").close()
            open(os.path.join(folder, ".nomedia"), "a").close()

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

                            ext = file_url.split(".")[-1]
                            fname = f"{tag}_{''.join(random.choices(string.ascii_letters + string.digits, k=6))}.{ext}"
                            fpath = os.path.join(folder, fname)

                            async with session.get(file_url) as f:
                                content = await f.read()
                                with open(fpath, "wb") as out:
                                    out.write(content)

                            await asyncio.sleep(random.randint(10, 20))  # пауза между файлами

                except Exception:
                    await asyncio.sleep(30)

            await asyncio.sleep(random.randint(40, 90))  # пауза между раундами

    async def stopfemburncmd(self, message):
        """Остановить мультифембой"""
        self.running = False
        await message.edit("🛑 Фембой-флуд остановлен.")