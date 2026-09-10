from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from random import choice
from database.requests import Database
from locales.uk_ua import Text_UA

import logging
logger = logging.getLogger(__name__)

async def check_and_send_birthdays(bot: Bot,
                                   db: Database):
    birthdays = await db.get_today_birthdays()
    if not birthdays:
        logger.info("No birthday was found today.")
        return
    logger.info(f"Found {len(birthdays)} people today.")
    for rec in birthdays:
        userid = rec['user_id']
        groupid = rec['group_id']
        name = rec['name']
        username = rec['username']

        mention = username if username else name
        text = choice(Text_UA.BIRTHDAY_MESSAGES).format(mention=mention)
        try:
            await bot.send_message(chat_id=groupid,
                                   text=text)
            logger.info(f"Sent message to {groupid}")
        except Exception as e:
            logger.exception("Error occured.")

async def send_tomorrow_remind(bot: Bot,
                               db: Database):
    reminders = await db.get_tomorrow_reminders()
    if not reminders:
        logger.info("No birthday was found tomorrow.")
        return
    for row in reminders:
        user_id = row['recipid']
        bday_name = row['bdayname']
        group = row['grouptitle']
        text = Text_UA.TOMORROW_MESSAGE.format(name=bday_name, group=group)
        try:
            await bot.send_message(chat_id=user_id, text=text)
            logger.info(f"Sent message to {user_id} (tomorrow birthday)")
        except (TelegramForbiddenError, TelegramBadRequest):
            pass
        except Exception as e:
            logger.exception("Error occured.")
