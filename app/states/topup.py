from aiogram.fsm.state import State, StatesGroup

class TopUp(StatesGroup):
    enter_amount = State()       # введення суми
    waiting_receipt = State()    # просимо чек, показуємо таймер і кнопку відміни/резюму
    awaiting_admin = State()     # чек на модерації у адміна
