import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from database import init_db
from handlers import router
from scheduler import check_reminders

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")


# ─── Keep-alive веб-сервер (чтобы Render не засыпал) ──────────────────────────
async def health(request):
    return web.Response(text="OK ✅")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()
    logger.info("Keep-alive сервер запущен на порту 10000")


# ─── Запуск ───────────────────────────────────────────────────────────────────
async def main():
    init_db()
    logger.info("База данных инициализирована")

    await start_web_server()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    asyncio.create_task(check_reminders(bot))
    logger.info("Планировщик запущен")

    logger.info("Бот запущен!")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
