from .start import router as start_router
from .callbacks import router as callbacks_router
from .admin import router as admin_router
from .admin_tools import router as admin_tools_router
from .balance import router as balance_router
from .shop import router as shop_router
from .topup import router as topup_router
from .admin_topup import router as admin_topup_router
from .admin_stock import router as admin_stock_router
from .admin_balance import router as admin_balance_router
from .fallback import router as fallback_router


def setup_routers(dp):
    dp.include_router(start_router)
    dp.include_router(callbacks_router)
    dp.include_router(shop_router)
    dp.include_router(topup_router)
    dp.include_router(admin_topup_router)
    dp.include_router(admin_stock_router)
    dp.include_router(admin_balance_router)
    from .admin_menu import router as admin_menu_router

    dp.include_router(admin_menu_router)
    dp.include_router(admin_router)
    dp.include_router(admin_tools_router)
    dp.include_router(balance_router)
    dp.include_router(fallback_router)
