from aiogram import Router, F
from aiogram.enums import ChatType
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command, CommandStart, CommandObject, StateFilter
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.fsm.context import FSMContext

from database.requests import Database
from utils.validate_birthdate import validate_birthdate
from locales.uk_ua import Text_UA

router = Router()

class BotMenu(StatesGroup):
    birthday_entering = State()


@router.message(CommandStart(), F.chat.type == ChatType.PRIVATE)
async def cmd_start(message: Message,
                    state: FSMContext,
                    db: Database):
    await message.reply(Text_UA.START.format(name=message.from_user.first_name))
    birthdate = await db.get_birthdate(message.from_user.id)
    if birthdate:
        await message.answer(Text_UA.BIRTHDAY_ALREADY.format(birthdate=f"{birthdate.day:02d}.{birthdate.month:02d}"))
    else:
        await message.answer(Text_UA.BIRTHDAY_ENTER)
    await state.set_state(BotMenu.birthday_entering)

@router.message(Command("cancel"), StateFilter(default_state), F.chat.type == ChatType.PRIVATE)
async def cancel_fail(message: Message):
    await message.answer(Text_UA.NOTHING_CANCELED,
                         reply_markup=ReplyKeyboardRemove())

@router.message(Command("cancel"), ~StateFilter(default_state), F.chat.type == ChatType.PRIVATE)
async def cancel_success(message: Message,
                         state: FSMContext):
    await state.clear()
    await message.answer(Text_UA.CANCELED,
                         reply_markup=ReplyKeyboardRemove())

@router.message(StateFilter(BotMenu.birthday_entering),
                ~F.text.startswith("/"),
                F.chat.type == ChatType.PRIVATE)
async def birthdate_process(message: Message,
                            state: FSMContext,
                            db: Database):
    user_date = validate_birthdate(message.text)
    if user_date is None:
        await message.answer(Text_UA.WRONG_FORMAT)
        return
    await db.change_birthdate(message.from_user.id, user_date)
    await message.answer(Text_UA.SUCCESS_BIRTHDATE)
    await state.clear()

async def build_privacy_kb(userid: int,
                           db: Database):
    groups = await db.get_user_groups_settings(userid)
    builder = InlineKeyboardBuilder()
    if not groups: return None
    for g in groups:
        icon = "🔒" if g['hide_birthdate'] else "🔓"
        button_text = f"{icon} {g['group_name']}"
        builder.button(text=button_text, callback_data=f"hide_{g['id']}")
    builder.adjust(1)
    return builder.as_markup()

@router.message(Command("hide"), F.chat.type == ChatType.PRIVATE)
async def cmd_hide_menu(message: Message,
                        db: Database):
    kb = await build_privacy_kb(message.from_user.id, db)
    if not kb:
        await message.answer(Text_UA.NO_GROUPS)
        return
    await message.answer(Text_UA.HIDE_MENU, reply_markup=kb)
@router.callback_query(F.data.startswith("hide_"))
async def callback_toggle_hide(callback: CallbackQuery,
                               db: Database):
    groupid = int(callback.data.split("_")[1])
    await db.toggle_hide_status(callback.from_user.id, groupid)
    new_kb = await build_privacy_kb(callback.from_user.id, db)
    try:
        await callback.message.edit_reply_markup(reply_markup=new_kb)
    except Exception:
        pass
    await callback.answer(Text_UA.HIDE_CHANGED)
