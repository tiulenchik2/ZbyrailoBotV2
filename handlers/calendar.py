from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import ChatType
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.requests import Database
from locales.uk_ua import Text_UA

router = Router()

def format_calendar_text(users, title_suff=""):
    '''
    Gets list of users and make it more beautiful
    '''
    if not users: return None
    months = Text_UA.MONTHS
    seasons = {
        12: '❄️', 1: '❄️', 2: '❄️', 
        3: '🌱', 4: '🌱', 5: '🌱',
        6: '☀️', 7: '☀️', 8: '☀️',
        9: '🍂', 10: '🍂', 11: '🍂'
    }
    text = Text_UA.CALENDAR_HEADER.format(group_title=title_suff)
    curr_month = None
    for user in users:
        bdate = user['birthdate']
        name = f"{user['name']} {user['surname']}" if user['surname'] else user['name']
        if bdate.month != curr_month:
            curr_month = bdate.month
            month_name = months.get(curr_month, "?")
            emoji = seasons.get(curr_month, "📅")
            text += f"\n{emoji} {month_name}\n"
        text += f"{bdate.day:02d}.{bdate.month:02d} - {name}\n"
    return text
async def show_calendar(message: Message,
                        db: Database,
                        userid: int = None,
                        is_edit: bool = False):
    real_userid = userid if userid else message.from_user.id
    if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        users = await db.get_birthdays_by_chatid(message.chat.id)
        text = format_calendar_text(users, title_suff=f"(chat {message.chat.title})")
        if not text:
            await message.answer(Text_UA.NO_BIRTHDAYS)
        else:
            await message.answer(text)
        return
    # user clicked command in pm
    groups = await db.get_user_groups(real_userid)
    if not groups:
        await message.answer(Text_UA.NO_GROUPS)
        return
    builder = InlineKeyboardBuilder()

    for g in groups:
        builder.button(text=f"🔸{g['group_title']}", callback_data=f"id_{g['id']}")
    builder.adjust(1)
    choose_message = Text_UA.CHOOSE_GROUP
    if is_edit:
        await message.edit_text(text=choose_message, reply_markup=builder.as_markup())
    else:
        await message.answer(text=choose_message, reply_markup=builder.as_markup())
@router.message(Command("calendar"))
async def cmd_calendar(message: Message,
                       db: Database):
    await show_calendar(message, db)


@router.callback_query(F.data.startswith("id_"))
async def callback_show_calendar(callback: CallbackQuery,
                                 db: Database):
    action = callback.data.split("_")[1]
    if action == "back":
        await show_calendar(callback.message,
                            db,
                            callback.from_user.id,
                            True)
        return
    groupid = int(action)
    users = await db.get_group_birthdays(groupid)
    text = format_calendar_text(users)
    if not text:
        await callback.answer(Text_UA.NO_BIRTHDAYS, show_alert=True)
        return
    back_kb = InlineKeyboardBuilder()
    back_kb.button(text=Text_UA.BUTTON_BACK, callback_data="id_back")

    await callback.message.edit_text(text, reply_markup=back_kb.as_markup())
    await callback.answer()
