from fastapi import FastAPI
from .database import Base, engine
from .users import router as users_router
from .routes.chat_routes import router as chat_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(users_router)
app.include_router(chat_router, prefix="/chat", tags=["chat"])
