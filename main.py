import asyncio
import asyncpg
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot, Dispatcher
import logging
from logging.handlers import TimedRotatingFileHandler
from os import makedirs
from database.requests import Database
from config import TOKEN, DATABASE
from utils.check_and_send import check_and_send_birthdays, send_tomorrow_remind
from handlers.user import router as user_router
from handlers.group import router as group_router
from handlers.calendar import router as calendar_router
from handlers.call import router as call_router
makedirs("logs", exist_ok=True)
file_handler = TimedRotatingFileHandler(
    filename="logs/bot",
    when="midnight",
    interval=1,
    backupCount=30,
    encoding="utf-8")
file_handler.suffix = "%Y_%m_d.log"
formatter = logging.Formatter("%(asctime)s - [%(levelname)s] - %(name)s - %(message)s")
file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logging.basicConfig(level=logging.INFO,
                    handlers=[file_handler, console_handler])
logger = logging.getLogger(__name__)
logger.info("Logging system initialised successfully.")

async def main():
    try:
        pool = await asyncpg.create_pool(dsn=DATABASE)
        logger.info("Database initialised successfully.")
    except Exception as e:
        logger.exception("Error occured when database was initialising.")
        return
    db = Database(pool)
    try:
        await db.create_tables()
        logger.info("Tables created.")
    except Exception as e:
        logger.exception("Erro occured while tables were creating!")
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_routers(user_router,
                       group_router,
                       calendar_router,
                       call_router)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_and_send_birthdays,
        trigger='cron',
        hour=8,
        minute=0,
        kwargs={'bot': bot, 'db': db}
    )
    scheduler.add_job(
        send_tomorrow_remind,
        trigger='cron',
        hour=19,
        minute=0,
        kwargs={'bot': bot, 'db': db}
    )
    scheduler.start()
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, db=db)
    finally:
        await pool.close()

if __name__ == '__main__':
    asyncio.run(main())