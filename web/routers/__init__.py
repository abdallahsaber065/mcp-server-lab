"""
Web Routers Package (web/routers/)
"""

from web.routers.admin import router as admin_router
from web.routers.auth import router as auth_router
from web.routers.chat import router as chat_router
from web.routers.leases import router as leases_router
from web.routers.maintenance import router as maintenance_router
from web.routers.mcp_protocol import router as mcp_protocol_router
from web.routers.memory import router as memory_router
from web.routers.notifications import router as notifications_router
from web.routers.properties import router as properties_router
from web.routers.showcase import router as showcase_router
from web.routers.state_graph import router as state_graph_router
from web.routers.logs import router as logs_router

__all__ = [
    "auth_router",
    "properties_router",
    "leases_router",
    "maintenance_router",
    "showcase_router",
    "state_graph_router",
    "admin_router",
    "chat_router",
    "memory_router",
    "mcp_protocol_router",
    "notifications_router",
    "logs_router"
]
