from app.presentation.routes.content.content_routes import router as content_router
from app.presentation.routes.content.gen_routes import router as gen_router
from app.presentation.routes.content.schedule_routes import router as schedule_router

__all__ = ["content_router", "gen_router", "schedule_router"]