# app/handlers/form.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.states.form import Form

router = Router()

@router.message(Command("form"))
async def start_form(message: Message, state: FSMContext):
    await state.set_state(Form.name)
    await message.answer("Введи своє ім’я:")

@router.message(Form.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.phone)
    await message.answer("Тепер введи свій номер телефону:")

@router.message(Form.phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    data = await state.get_data()
    await message.answer(
        f"Дякую!\nІм’я: {data['name']}\nТелефон: {data['phone']}"
    )
    await state.clear()
