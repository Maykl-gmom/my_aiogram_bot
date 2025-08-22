from aiogram.fsm.state import StatesGroup, State

class Shop(StatesGroup):
    choosing_category = State()
    choosing_product = State()
    confirming = State()
    reserved = State()         # резерв створено, чекаємо квитанцію
    waiting_receipt = State()  # очікуємо квитанцію (фото/повідомлення)
    awaiting_admin = State()   # чек пішов адміну, чекаємо рішення
