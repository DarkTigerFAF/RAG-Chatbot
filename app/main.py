from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
import os
from .core import config as _config  # ensure .env is loaded before anything else
from .core.database import Base, engine
from .api.routes.auth import router as auth_router
from .api.routes.chat import router as chat_router

Base.metadata.create_all(bind=engine)

app = FastAPI(default_response_class=ORJSONResponse)
app.add_middleware(GZipMiddleware, minimum_size=500)

# CORS configuration (set CORS_ORIGINS in .env as comma-separated list or "*")
_origins_env = os.getenv("CORS_ORIGINS", "*").strip()
if _origins_env == "*":
	_allowed_origins = ["*"]
else:
	_allowed_origins = [o.strip() for o in _origins_env.split(",") if o.strip()]

app.add_middleware(
	CORSMiddleware,
	allow_origins=_allowed_origins,
	allow_credentials=True,
	allow_methods=["*"],    
	allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(chat_router, prefix="/chat", tags=["chat"])
