from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from app.utils.telegram import safe_answer

from app.utils.balance import get_balance
from app.keyboards.main import main_menu_kb
from app.utils.files import read_products
from app.utils.inventory import available_products_map
from app.keyboards.shop import categories_kb
from app.states.shop import Shop
from aiogram.fsm.context import FSMContext

router = Router()

@router.message(CommandStart())
async def on_start(message: Message, state: FSMContext):
    bal = get_balance(message.from_user.id)
    await message.answer(
        f'Привіт, <a href="tg://user?id={message.from_user.id}">{message.from_user.full_name}</a>\n'
        f'Ваш баланс: <b>{bal} грн</b>',
        reply_markup=main_menu_kb()
    )
    await state.clear()

# Кнопка «Список категорій» відкриває поточну логіку магазину
@router.callback_query(F.data == "main:cats")
async def open_categories(callback: CallbackQuery, state: FSMContext):
    catalog = read_products()
    available = available_products_map(catalog)
    if not available:
        await callback.message.edit_text("Наразі всі товари відсутні на складі.")
        await state.clear()
    else:
        await callback.message.edit_text("Оберіть категорію:", reply_markup=categories_kb(list(available.keys())))
        await state.set_state(Shop.choosing_category)
    await safe_answer(callback)
