from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
import time
import os

from app.states.shop import Shop
from app.utils.files import read_products
from app.utils.inventory import (
    available_products_map,
    reserve_first_file,
    cancel_reservation,
    has_stock,
    complete_reservation,
    fetch_active_reservation_for_user,
)
from app.keyboards.shop import (
    categories_kb,
    products_kb,
    pay_or_cancel_kb,
    confirm_with_balance_kb,
)
from app.keyboards.admin import admin_review_kb
from app.config import get_admin_id, get_card_number
from app.utils.balance import get_balance, add_balance
from app.keyboards.main import main_menu_kb
from app.utils.telegram import safe_answer

router = Router()


# === Відкриття магазину ===
@router.message(Command("shop"))
@router.message(F.text.lower().in_({"магазин", "shop"}))
async def open_shop(message: Message, state: FSMContext):
    catalog = read_products()
    available = available_products_map(catalog)
    if not available:
        await message.answer("Наразі всі товари відсутні на складі.")
        await state.clear()
        return
    cats = list(available.keys())
    await state.update_data(catalog=catalog)
    await message.answer("Оберіть категорію:", reply_markup=categories_kb(cats))
    await state.set_state(Shop.choosing_category)


# === Вибір категорії ===
@router.callback_query(Shop.choosing_category, F.data.startswith("cat:"))
async def choose_category(callback: CallbackQuery, state: FSMContext):
    catalog = read_products()
    available = available_products_map(catalog)
    cat = callback.data.split("cat:", 1)[1]
    if cat not in available:
        cats = list(available.keys())
        if not cats:
            await callback.message.edit_text("Наразі всі товари відсутні на складі.")
            await state.clear()
            await safe_answer(callback)
            return
        await callback.message.edit_text(
            "Ця категорія зараз порожня. Оберіть іншу:",
            reply_markup=categories_kb(cats),
        )
        await state.set_state(Shop.choosing_category)
        await safe_answer(callback)
        return

    products = available[cat]
    await state.update_data(category=cat, visible_products=products)
    await callback.message.edit_text(
        f"Категорія: <b>{cat}</b>\nОбери товар:",
        reply_markup=products_kb(products),
    )
    await state.set_state(Shop.choosing_product)
    await safe_answer(callback)


# === Назад до списку категорій ===
@router.callback_query(Shop.choosing_product, F.data == "back:cats")
async def back_to_categories(callback: CallbackQuery, state: FSMContext):
    catalog = read_products()
    available = available_products_map(catalog)
    if not available:
        await callback.message.edit_text("Наразі всі товари відсутні на складі.")
        await state.clear()
        await safe_answer(callback)
        return
    await callback.message.edit_text(
        "Оберіть категорію:",
        reply_markup=categories_kb(list(available.keys())),
    )
    await state.set_state(Shop.choosing_category)
    await safe_answer(callback)


# === Вибір товару ===
@router.callback_query(Shop.choosing_product, F.data.startswith("prod:"))
async def choose_product(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    products = data.get("visible_products") or []
    try:
        idx = int(callback.data.split("prod:", 1)[1])
        name, price = products[idx]
    except Exception:
        await safe_answer(callback, "Невідомий товар", show_alert=True)
        return

    cat = data.get("category")
    if not has_stock(cat, name):
        catalog = read_products()
        available = available_products_map(catalog)
        if cat not in available:
            cats = list(available.keys())
            if not cats:
                await callback.message.edit_text("Наразі всі товари відсутні на складі.")
                await state.clear()
                await safe_answer(callback, "Товар закінчився")
                return
            await callback.message.edit_text(
                "Товар закінчився. Оберіть іншу категорію:",
                reply_markup=categories_kb(cats),
            )
            await state.set_state(Shop.choosing_category)
        else:
            new_products = available[cat]
            await state.update_data(visible_products=new_products)
            await callback.message.edit_text(
                f"Категорія: <b>{cat}</b>\nОновлений список товарів:",
                reply_markup=products_kb(new_products),
            )
            await state.set_state(Shop.choosing_product)
        await safe_answer(callback, "Товар закінчився")
        return

    await state.update_data(product_name=name, product_price=price)
    await callback.message.edit_text(
        f"Ви вибрали: <b>{name}</b>\nЦіна: <b>{price} грн</b>\n\nОбери дію:",
        reply_markup=confirm_with_balance_kb(),
    )
    await state.set_state(Shop.confirming)
    await safe_answer(callback)


# === Скасування підтвердження ===
@router.callback_query(Shop.confirming, F.data == "cancel")
async def cancel_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cat = data.get("category")
    catalog = read_products()
    available = available_products_map(catalog)

    if cat in available:
        products = available[cat]
        await state.update_data(visible_products=products)
        await callback.message.edit_text(
            "Скасовано. Обери інший товар:",
            reply_markup=products_kb(products),
        )
        await state.set_state(Shop.choosing_product)
    else:
        cats = list(available.keys())
        if not cats:
            await callback.message.edit_text("Наразі всі товари відсутні на складі.")
            await state.clear()
        else:
            await callback.message.edit_text(
                "Оберіть категорію:",
                reply_markup=categories_kb(cats),
            )
            await state.set_state(Shop.choosing_category)

    await safe_answer(callback)


# === Оплата карткою: оформлення резерву ===
@router.callback_query(Shop.confirming, F.data == "confirm")
async def confirm_order_card(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cat = data.get("category")
    name = data.get("product_name")
    user_id = callback.from_user.id

    reservation = reserve_first_file(cat, name, user_id)
    if not reservation:
        catalog = read_products()
        available = available_products_map(catalog)
        if cat in available and available[cat]:
            products = available[cat]
            await state.update_data(visible_products=products)
            await callback.message.edit_text(
                "На жаль, товар щойно розібрали. Оберіть інший:",
                reply_markup=products_kb(products),
            )
            await state.set_state(Shop.choosing_product)
        else:
            cats = list(available.keys())
            if not cats:
                await callback.message.edit_text("Наразі всі товары відсутні на складі.")
                await state.clear()
            else:
                await callback.message.edit_text(
                    "У цій категорії зараз порожньо. Оберіть іншу:",
                    reply_markup=categories_kb(cats),
                )
                await state.set_state(Shop.choosing_category)
        await safe_answer(callback, "Товар недоступний")
        return

    remain = max(0, reservation.expires_at - int(time.time()))
    mins, secs = divmod(remain, 60)
    card = get_card_number()

    await state.update_data(reservation_id=reservation.id)
    await callback.message.edit_text(
        f"✅ Резерв оформлено: <b>{name}</b>\n"
        f"Час резервації товару: <b>{mins} хв {secs} с</b>\n"
        f"Карта для поповнення: <code>{card}</code>",
        reply_markup=pay_or_cancel_kb("reserve"),
    )
    await state.set_state(Shop.reserved)
    await safe_answer(callback)


# === Спроба оплатити з балансу із екрана підтвердження ===
@router.callback_query(Shop.confirming, F.data == "paybal:try")
async def try_pay_by_balance(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    price = int(data.get("product_price", 0))
    name = data.get("product_name")
    cat = data.get("category")
    uid = callback.from_user.id

    bal = get_balance(uid)
    lack = max(0, price - bal)

    if lack > 0:
        # пропонуємо автопоповнення рівно на нестачу (але не менше 100)
        suggest = lack if lack >= 100 else 100
        from aiogram.utils.keyboard import InlineKeyboardBuilder

        kb = InlineKeyboardBuilder()
        kb.button(text=f"Поповнити на {suggest} грн", callback_data=f"topup:auto:{suggest}")
        kb.button(text="⬅️ Назад", callback_data="back:confirm")
        kb.adjust(1)
        await callback.message.edit_text(
            f"❌ Недостатньо коштів на балансі.\n"
            f"Ціна товару: <b>{price} грн</b>\n"
            f"Ваш баланс: <b>{bal} грн</b>\n"
            f"Бракує: <b>{lack} грн</b>\n\n"
            f"Можу створити заявку на поповнення на <b>{suggest} грн</b> прямо зараз.",
            reply_markup=kb.as_markup(),
        )
        await safe_answer(callback)
        return

    # Грошей вистачає: резервуємо і списуємо баланс
    if not has_stock(cat, name):
        await safe_answer(callback, "Товар щойно закінчився", show_alert=True)
        return
    res = reserve_first_file(cat, name, uid)
    if not res:
        await safe_answer(callback, "Не встигли, спробуйте інший товар", show_alert=True)
        return

    new_bal = add_balance(uid, -price)
    dest_path = complete_reservation(res.id)

    # повідомляємо адміна про продаж з балансу
    try:
        await callback.message.bot.send_message(
            chat_id=get_admin_id(),
            text=(
                "💸 Продаж з балансу\n"
                f"Клієнт: {callback.from_user.full_name} (id={uid})\n"
                f"Товар: {name}\n"
                f"Сума: {price} грн\n"
                f"Баланс після списання: {new_bal} грн"
            ),
        )
    except Exception:
        pass

    # віддаємо файл, якщо існує; інакше — текст
    if dest_path and os.path.isfile(dest_path):
        try:
            await callback.message.answer_document(
                FSInputFile(dest_path),
                caption=f"✅ Оплачено з балансу. Залишок: {new_bal} грн",
            )
        except Exception:
            await callback.message.answer(f"✅ Оплачено з балансу. Залишок: <b>{new_bal} грн</b>")
    else:
        await callback.message.answer(f"✅ Оплачено з балансу. Залишок: <b>{new_bal} грн</b>")

    await callback.message.answer("Повертаю в головне меню.", reply_markup=main_menu_kb())
    await state.clear()
    await safe_answer(callback, "Оплачено")


# === Назад із екрану браку коштів ===
@router.callback_query(F.data == "back:confirm")
async def back_to_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    name = data.get("product_name")
    price = data.get("product_price")
    await callback.message.edit_text(
        f"Ви вибрали: <b>{name}</b>\nЦіна: <b>{price} грн</b>\n\nОбери дію:",
        reply_markup=confirm_with_balance_kb(),
    )
    await state.set_state(Shop.confirming)
    await safe_answer(callback)


# === Кнопка «Оплатив» у блоці товару (просимо чек) ===
@router.callback_query(Shop.reserved, F.data == "pay:reserve")
async def reserve_paid(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Надішліть квитанцію про оплату (фото/скриншот) у відповідь на це повідомлення."
    )
    await state.set_state(Shop.waiting_receipt)
    await safe_answer(callback)


# === Прийом квитанції (товар) ===
@router.message(Shop.waiting_receipt, F.photo)
async def receipt_photo_in_state(message: Message, state: FSMContext):
    data = await state.get_data()
    res_id = data.get("reservation_id")
    if not res_id:
        await message.answer("Щось пішло не так із резервом.")
        await state.clear()
        return
    admin_id = get_admin_id()
    await message.forward(admin_id)
    await message.bot.send_message(
        chat_id=admin_id,
        text=(
            f"Квитанція від {message.from_user.full_name} "
            f"(id={message.from_user.id})\nРезерв ID: {res_id}"
        ),
        reply_markup=admin_review_kb(int(res_id), int(message.from_user.id)),
    )
    await message.answer("Квитанцію надіслано на перевірку адміну. Очікуйте рішення.")
    await state.set_state(Shop.awaiting_admin)


@router.message(Shop.waiting_receipt, F.text)
async def receipt_text(message: Message, state: FSMContext):
    await message.answer("Будь ласка, надішліть фото/скриншот квитанції.")


# === Глобальне скасування резерву ===
@router.callback_query(F.data == "reserve:cancel")
async def cancel_reserve_global(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    res_id = data.get("reservation_id")
    if not res_id:
        res = fetch_active_reservation_for_user(callback.from_user.id)
        res_id = res.id if res else None
    if res_id and cancel_reservation(int(res_id)):
        bal = get_balance(callback.from_user.id)
        await callback.message.edit_text(
            f"Резерв скасовано.\nВаш баланс: <b>{bal} грн</b>",
            reply_markup=main_menu_kb(),
        )
    else:
        await callback.message.edit_text(
            "Не вдалося скасувати резерв. Можливо, він вже завершений."
        )
    await state.clear()
    await safe_answer(callback)


# === Відновити активний резерв (кнопка) ===
@router.callback_query(F.data == "reserve:resume")
async def resume_reservation_cb(callback: CallbackQuery, state: FSMContext):
    r = fetch_active_reservation_for_user(callback.from_user.id)
    if not r:
        await callback.answer("Активних резервацій немає", show_alert=True)
        return

    await state.update_data(reservation_id=r.id, category=r.category, product_name=r.product)
    remain = max(0, r.expires_at - int(time.time()))
    mins, secs = divmod(remain, 60)

    await callback.message.edit_text(
        f"🔒 Активний резерв: <b>{r.product}</b>\n"
        f"Залишилось: <b>{mins} хв {secs} с</b>\n"
        f"Карта для оплати: <code>{get_card_number()}</code>",
        reply_markup=pay_or_cancel_kb("reserve"),
    )
    await state.set_state(Shop.reserved)
    await safe_answer(callback)


# === Відновити активний резерв (команда /resume) ===
@router.message(Command("resume"))
async def resume_reservation_cmd(message: Message, state: FSMContext):
    r = fetch_active_reservation_for_user(message.from_user.id)
    if not r:
        await message.answer("Активних резервацій немає.")
        return

    await state.update_data(reservation_id=r.id, category=r.category, product_name=r.product)
    remain = max(0, r.expires_at - int(time.time()))
    mins, secs = divmod(remain, 60)

    await message.answer(
        f"🔒 Активний резерв: <b>{r.product}</b>\n"
        f"Залишилось: <b>{mins} хв {secs} с</b>\n"
        f"Карта для оплати: <code>{get_card_number()}</code>",
        reply_markup=pay_or_cancel_kb("reserve"),
    )
    await state.set_state(Shop.reserved)
