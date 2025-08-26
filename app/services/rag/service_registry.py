from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.model_config import ChatService
from ...schemas.chat import ModelConfig


def load_model_cfg(db: Session, service_id: str) -> ModelConfig | None:
    svc = db.query(ChatService).filter_by(service_id=service_id).first()
    if not svc:
        return None
    return ModelConfig(
        service_id=svc.service_id,
        chat_deployment=svc.chat_deployment,
    )
