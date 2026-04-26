from .auth import router as auth_router
from .teams import router as teams_router
from .subteams import router as subteams_router
from .players import router as players_router
from .users import router as users_router
from .tournaments import router as tournaments_router
from .matches import router as matches_router
from .player_match_stats import router as player_match_stats_router

__all__ = [
    "auth_router", "teams_router", "subteams_router",
    "players_router", "users_router",
    "tournaments_router", "matches_router",
    "player_match_stats_router",
] 