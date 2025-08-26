from sqlalchemy import Column, Integer, String
from app.core.database import Base

class ChatService(Base):
    __tablename__ = "chat_services"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(String, unique=True, index=True, nullable=False)  
    chat_deployment = Column(String, nullable=False)
