from .auth import router as auth_router
from .teams import router as teams_router
from .subteams import router as subteams_router
from .players import router as players_router
from .users import router as users_router

__all__ = ["auth_router", "teams_router", "subteams_router", "players_router", "users_router"] 