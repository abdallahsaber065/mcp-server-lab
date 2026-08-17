"""
Web Routers Package (web/routers/)
"""

from web.routers.auth import router as auth_router
from web.routers.properties import router as properties_router
from web.routers.leases import router as leases_router
from web.routers.maintenance import router as maintenance_router
from web.routers.showcase import router as showcase_router
from web.routers.state_graph import router as state_graph_router
from web.routers.admin import router as admin_router

__all__ = [
    "auth_router",
    "properties_router",
    "leases_router",
    "maintenance_router",
    "showcase_router",
    "state_graph_router",
    "admin_router"
]
