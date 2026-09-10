import asyncio

from telethon import TelegramClient
from database.requests import Database

from config import TOKEN, API_ID, API_HASH

async def sync_group_members(chatid: int, db: Database):
    '''
    Parses all members of group and writes into database
    '''
    async with TelegramClient('bot_session', int(API_ID), API_HASH) as cli:
        await cli.start(bot_token=TOKEN)
        entity = await cli.get_entity(chatid)
        grouptitle = entity.title
        members = []
        async for member in cli.iter_participants(chatid, aggressive=True):
            if member.bot: continue
            members.append((member.id,
                        member.username,
                        member.first_name,
                        member.last_name,
                        None))
        if members:
            await db.create_rows(members, chatid, grouptitle)
    return members
