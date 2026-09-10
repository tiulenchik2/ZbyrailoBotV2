import asyncio
from aiogram import Router, html, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandObject
from aiogram.enums import ChatType, ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.requests import Database
from locales.uk_ua import Text_UA
from random import choice

router = Router()

GROUP_ONLY = F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP})
SAFE_LIMIT = 30
pending_calls = {}

async def execute_call(message: Message,
                       targets: list,
                       header: str):
    chunk_size = 5
    invisible_char = "\u200b"
    for i in range(0, len(targets), chunk_size):
        chunk = targets[i:i+chunk_size]
        hidden_mentions = ""
        for user in chunk:
            user_id = user['user_id']
            hidden_mentions += html.link(invisible_char, f"tg://user?id={user_id}")
        await message.answer(f"{header}{hidden_mentions}", parse_mode=ParseMode.HTML)
@router.message(Command('reg'), GROUP_ONLY)
async def call_reg(message: Message,
                   db: Database):
    await db.set_call(message.from_user.id, message.chat.id, True)
    await message.reply(Text_UA.REG)
@router.message(Command('unreg'), GROUP_ONLY)
async def call_unreg(message: Message,
                   db: Database):
    await db.set_call(message.from_user.id, message.chat.id, False)
    await message.reply(Text_UA.UNREG)
@router.message(Command("call"), GROUP_ONLY)
async def call(message: Message,
               command: CommandObject,
               db: Database):
    try: await message.delete()
    except: pass
    subs = await db.get_call_regs(message.chat.id)
    targets = [s for s in subs if s['user_id'] != message.from_user.id]
    if not targets:
        await message.answer(Text_UA.NO_CALL)
        await asyncio.sleep(5)
        await message.delete()
        return
    call_reason = html.quote(command.args) if command.args else choice(Text_UA.NO_REASON_HEADERS)
    caller = html.link(message.from_user.first_name, f"tg://user?id={message.from_user.id}")
    header = f"📢 {caller}: {call_reason}" if command.args else f"📢 {caller} {call_reason}"
    if len(targets) > SAFE_LIMIT:
        pending_calls[message.from_user.id] = {
            'header': header,
            'targets': targets
        }
        builder = InlineKeyboardBuilder()
        builder.button(text=Text_UA.YES, callback_data=f"confirm_yes_{message.from_user.id}")
        builder.button(text=Text_UA.NO, callback_data=f"confirm_no_{message.from_user.id}")
        confirm_text = f"😮{choice(Text_UA.CONFIRM_CALL_HEADERS)}{Text_UA.CONFIRM_CALL}"
        await message.answer(confirm_text,
                             reply_markup=builder.as_markup())
        return
    await execute_call(message, targets, header)
@router.callback_query(F.data.startswith("confirm_"))
async def confirmation(callback: CallbackQuery):
    parts = callback.data.split("_")
    action = parts[1]
    caller = int(parts[2])
    if callback.from_user.id != caller:
        await callback.answer(Text_UA.WRONG_CALLER)
        return
    if action == "no":
        await callback.message.delete()
        pending_calls.pop(caller, None)
        await callback.answer(Text_UA.CANCELED_CALL)
        return
    if action == "yes":
        await callback.message.delete()
        data = pending_calls.pop(caller, None)
        if not data:
            await callback.answer(Text_UA.RUNOUT)
            return
        await execute_call(callback.message, data['targets'], data['header'])
        await callback.answer()
