from aiogram.fsm.state import StatesGroup, State

class Balance(StatesGroup):
    entering_amount = State()
    confirming = State()       # новий стан: підтвердити/скасувати суму
    awaiting_admin = State()
