import asyncio
from aiogram import Router, Bot, F
from aiogram.types import ChatMemberUpdated, Message
from aiogram.filters import ChatMemberUpdatedFilter, KICKED, LEFT, RESTRICTED, MEMBER, ADMINISTRATOR

from database.requests import Database
from utils.sync_group import sync_group_members
from locales.uk_ua import Text_UA

import logging
logger = logging.getLogger(__name__)

router = Router()

async def background_sync(chatid: int, db: Database, bot: Bot):
    try:
        await sync_group_members(chatid, db)
        logger.info(f"Users in group {chatid} synced.")
    except Exception as e:
        logger.exception("Error occured while users were syncing.")

@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=(KICKED | LEFT | RESTRICTED)>>(MEMBER | ADMINISTRATOR)))
async def on_bot_joined(event: ChatMemberUpdated, db: Database, bot: Bot):
    chat_title = event.chat.title or "Untitled Group"
    await db.add_group(event.chat.id, chat_title)
    await event.answer(Text_UA.GREETING)
    asyncio.create_task(background_sync(event.chat.id, db, bot))

@router.message(F.new_chat_members)
async def welcome_newcomer(message: Message,
                           db: Database):
      newcomers = []
      for new_user in message.new_chat_members:
        if new_user.is_bot: continue
        user_tuple = (
                  new_user.id,
                  new_user.username,
                  new_user.first_name,
                  new_user.last_name,
                  None
            )
        newcomers.append(user_tuple)
        if newcomers:
            try:
                chat_title = message.chat.title or "Untitled Group"
                 await db.create_rows(newcomers,
                                       message.chat.id,
                                       chat_title)
                 logger.info(f"{len(newcomers)} newcomers were added.")
            except Exception as e:
                  logger.exception("Error occured while adding newcomers.")
@router.message(F.left_chat_members)
async def user_left_chat(message: Message,
                         db: Database):
    left = message.left_chat_member
    bot_obj = await message.bot.get_me()
    if left.id == bot_obj.id:
        logging.warning(f"Bot was deleted from {message.chat.id}")
        return
    try:
        await db.remove_user(left.id, message.chat.id)
        logger.info(f"{left.id} was deleted from group {message.chat.id}")
    except Exception as e:
        logger.exception("Error occured while deleting left users.")
