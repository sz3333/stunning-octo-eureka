from .. import loader, utils
import aiohttp
import asyncio
import random

@loader.tds
class MultiFemburnTGMod(loader.Module):
    """Отправка артов e621 по тегам (указывать через ; и количество)"""

    strings = {"name": "MultiFemburnTG"}

    def __init__(self):
        self.running = False

    async def multifemburncmd(self, message):
        """Использование: .multifemburn тэг;тэг;тэг количество"""
        args = utils.get_args_raw(message).split()
        if len(args) < 2:
            await message.edit("❌ Используй: `.multifemburn femboy;catboy 5`")
            return

        tags = args[0].split(";")
        try:
            count = int(args[1])
        except ValueError:
            await message.edit("❌ Количество должно быть числом")
            return

        self.running = True
        await message.edit(f"🧦 Отправляю {count} артов по тегам: {', '.join(tags)}")

        asyncio.create_task(self._send_posts(message, tags, count))

    async def _send_posts(self, message, tags, count):
        headers = {"User-Agent": "HikkaBot/1.0 by Lidik"}
        sent = 0

        async with aiohttp.ClientSession() as session:
            while self.running and sent < count:
                for tag in tags:
                    if sent >= count or not self.running:
                        break

                    url = f"https://e621.net/posts.json?tags={tag}+order:random&limit=1"

                    try:
                        async with session.get(url, headers=headers) as resp:
                            if resp.status != 200:
                                await asyncio.sleep(10)
                                continue

                            data = await resp.json()
                            posts = data.get("posts", [])

                            for post in posts:
                                file_url = post.get("file", {}).get("url")
                                if not file_url:
                                    continue

                                try:
                                    await message.client.send_file(
                                        message.chat_id,
                                        file_url,
                                        caption=f"🎨 Тег: {tag}"
                                    )
                                    sent += 1
                                except Exception:
                                    continue

                                await asyncio.sleep(random.randint(5, 10))  # пауза
                    except Exception:
                        await asyncio.sleep(5)

        await message.respond("✅ Отправка завершена.")

    async def stopfemburncmd(self, message):
        """Остановить отправку"""
        self.running = False
        await message.edit("🛑 Отправка остановлена.")