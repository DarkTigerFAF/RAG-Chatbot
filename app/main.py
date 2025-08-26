from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from .core import config as _config  # ensure .env is loaded before anything else
from .core.database import Base, engine
from .api.routes.auth import router as auth_router
from .api.routes.chat import router as chat_router

Base.metadata.create_all(bind=engine)

app = FastAPI(default_response_class=ORJSONResponse)
app.add_middleware(GZipMiddleware, minimum_size=500)
app.include_router(auth_router)
app.include_router(chat_router, prefix="/chat", tags=["chat"])
