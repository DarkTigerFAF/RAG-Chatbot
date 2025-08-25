from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.model_config import ChatService
from ...schemas.chat import ModelConfig as ModelCfgModel


def load_model_cfg(db: Session, service_id: str) -> ModelCfgModel | None:
    svc = db.query(ChatService).filter_by(service_id=service_id).first()
    if not svc:
        return None
    return ModelCfgModel(
        service_id=svc.service_id,
        chat_deployment=svc.chat_deployment,
        endpoint=svc.endpoint,
        api_key=svc.api_key,
        api_version=svc.api_version,
    )
