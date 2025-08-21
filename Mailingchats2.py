# meta developer: @LidF1x
# meta name: UniversalMailing
# meta desc: |
#   📂 Универсальная рассылка по папкам Telegram
#   🔹 Добавляй папки по ID
#   🔹 Рассылка во все включённые чаты
#   🔹 Сейф-режим, лимиты и задержки от бана

from .. import loader, utils
import asyncio, time, random, logging
from telethon.tl.functions.messages import GetDialogFiltersRequest
from telethon.tl.types import DialogFilter, Peer

logger = logging.getLogger(__name__)

@loader.tds
class UniversalMailingMod(loader.Module):
    """Универсальная рассылка по папкам Telegram"""
    
    strings = {
        "name": "UniversalMailing",
        "loading": "📂 UniversalMailing загружен! Используйте .msgo <время> <интервал> <текст>",
        "start": "🚀 Рассылка запущена в {} чатов | Интервал: {} сек",
        "stop": "🛑 Рассылка остановлена",
        "done": "✅ Завершено | Отправлено: {}",
        "args_error": "❌ Используйте: .msgo <время> <интервал> <текст>",
        "num_error": "❌ Время и интервал должны быть числами",
        "no_chats": "❌ Нет чатов для рассылки. Добавьте папки с чатами",
        "folder_added": "✅ Папка добавлена: {}",
        "folder_exists": "⚠️ Папка уже в списке",
        "folder_removed": "✅ Папка удалена: {}",
        "folder_not_found": "⚠️ Папка не найдена",
        "folders_list": "📋 Папки для рассылки: {}",
        "stats": "📊 Статистика:\nОтправлено: {}\nОшибок: {}\nЛимит: {}/час",
        "protection": "🛡️ Защита от бана: {}",
        "protection_on": "ВКЛЮЧЕНА",
        "protection_off": "ВЫКЛЮЧЕНА"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "ms_folders",
                [],
                lambda: "Список ID папок для рассылки",
                validator=loader.validators.Series(
                    validator=loader.validators.Integer()
                )
            ),
            loader.ConfigValue(
                "ms_protection",
                True,
                lambda: "Защита от бана",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "ms_limit",
                180,
                lambda: "Лимит сообщений в час",
                validator=loader.validators.Integer(minimum=50, maximum=500)
            )
        )
        self.active = False
        self.sent = 0
        self.errors = 0
        self.last_send = 0
        self.hourly_count = 0
        self.last_hour = time.time()

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        await self.client.send_message("me", self.strings["loading"])

    async def _get_chats_from_folders(self):
        """Берём все включённые чаты из выбранных папок"""
        res = await self.client(GetDialogFiltersRequest())
        chats = []
        for f in res.filters:
            if not isinstance(f, DialogFilter):
                continue
            if f.id in self.config["ms_folders"]:
                peers = (f.pinned_peers or []) + (f.include_peers or [])
                for p in peers:
                    if isinstance(p, Peer):
                        chats.append(p)
        return list(set(chats))

    @loader.command()
    async def msgo(self, message):
        """Запуск рассылки: .msgo <время> <интервал> <текст>"""
        if self.active:
            await utils.answer(message, "❗ Рассылка уже активна")
            return

        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings["args_error"])
            return

        try:
            args = args.split(" ", 2)
            duration = int(args[0])
            interval = max(int(args[1]), 5)
            text = args[2]
        except:
            await utils.answer(message, self.strings["num_error"])
            return

        chats = await self._get_chats_from_folders()
        if not chats:
            await utils.answer(message, self.strings["no_chats"])
            return

        self.active = True
        self.sent = 0
        self.errors = 0

        await utils.answer(message, self.strings["start"].format(len(chats), interval))

        end_time = time.time() + duration
        while self.active and time.time() < end_time:
            await self._send_to_chats(chats, text)
            if self.active and time.time() < end_time:
                await asyncio.sleep(interval)

        if self.active:
            await utils.answer(message, self.strings["done"].format(self.sent))
        self.active = False

    @loader.command()
    async def msstop(self, message):
        """Остановка рассылки"""
        self.active = False
        await utils.answer(message, self.strings["stop"])

    @loader.command()
    async def msfadd(self, message):
        """Добавить папку: .msfadd <id>"""
        try:
            folder_id = int(utils.get_args_raw(message))
        except:
            await utils.answer(message, "ℹ️ Укажите ID папки числом")
            return
        if folder_id in self.config["ms_folders"]:
            await utils.answer(message, self.strings["folder_exists"])
            return
        self.config["ms_folders"].append(folder_id)
        await utils.answer(message, self.strings["folder_added"].format(folder_id))

    @loader.command()
    async def msfdel(self, message):
        """Удалить папку: .msfdel <id>"""
        try:
            folder_id = int(utils.get_args_raw(message))
        except:
            await utils.answer(message, "ℹ️ Укажите ID папки числом")
            return
        if folder_id not in self.config["ms_folders"]:
            await utils.answer(message, self.strings["folder_not_found"])
            return
        self.config["ms_folders"].remove(folder_id)
        await utils.answer(message, self.strings["folder_removed"].format(folder_id))

    @loader.command()
    async def msflist(self, message):
        """Список папок"""
        if not self.config["ms_folders"]:
            await utils.answer(message, "ℹ️ Нет добавленных папок")
            return
        await utils.answer(message, self.strings["folders_list"].format(
            ", ".join(str(f) for f in self.config["ms_folders"])
        ))

    @loader.command()
    async def msstats(self, message):
        """Статистика"""
        status = self.strings["protection_on"] if self.config["ms_protection"] else self.strings["protection_off"]
        stats = self.strings["stats"].format(self.sent, self.errors, self.hourly_count)
        await utils.answer(message, stats + "\n" + self.strings["protection"].format(status))

    @loader.command()
    async def msmode(self, message):
        """Режим защиты"""
        self.config["ms_protection"] = not self.config["ms_protection"]
        status = self.strings["protection_on"] if self.config["ms_protection"] else self.strings["protection_off"]
        await utils.answer(message, self.strings["protection"].format(status))

    async def _send_to_chats(self, chats, text):
        self._check_limits()
        for peer in chats:
            if not self.active:
                break
            await self._safe_send(peer, text)

    async def _safe_send(self, peer, text):
        try:
            if self.config["ms_protection"]:
                delay = random.uniform(2.5, 6.0)
                if time.time() - self.last_send < 10:
                    delay += random.uniform(1.0, 3.0)
                await asyncio.sleep(delay)
            await self.client.send_message(peer, text)
            self.sent += 1
            self.hourly_count += 1
            self.last_send = time.time()
        except Exception as e:
            self.errors += 1
            if "Too Many Requests" in str(e) and self.config["ms_protection"]:
                wait = random.randint(45, 180)
                await asyncio.sleep(wait)
                return await self._safe_send(peer, text)

    def _check_limits(self):
        now = time.time()
        if now - self.last_hour > 3600:
            self.hourly_count = 0
            self.last_hour = now

    async def on_unload(self):
        self.active = False