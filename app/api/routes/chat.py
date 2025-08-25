from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.model_config import ChatService


from ...core.database import get_db
from ...schemas.chat import (
    ChatRequest,
    ChatResponse,
    HistoryPair,
    ModelConfig,
    ChatServiceCreateResponse,
)
from ...services.rag.factory import rag_chat
from ...models.user import User
from ...models.history import History
from ..deps import get_current_user


router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    model: str = Query(...),
) -> ChatResponse:
    try:
        answer = await rag_chat(db, user.id, req.query, model)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
    return {"answer": answer}


@router.get("/history", response_model=list[HistoryPair])
def get_history(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[HistoryPair]:
    rows = (
        db.query(History)
        .filter(History.user_id == current_user.id)
        .order_by(History.timestamp.desc())
        .all()
    )

    return [
        HistoryPair(
            question=h.question,
            answer=h.answer,
            created_at=h.timestamp,
        )
        for h in rows
    ]


@router.post("/service", response_model=ChatServiceCreateResponse)
def create_chat_service(
    req: ModelConfig,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> ChatServiceCreateResponse:
    svc = ChatService(
        service_id=req.service_id,
        chat_deployment=req.chat_deployment,
        endpoint=req.endpoint,
        api_key=req.api_key.get_secret_value(),
        api_version=req.api_version,
    )
    db.add(svc)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="service_id already exists")
    db.refresh(svc)
    return ChatServiceCreateResponse(created=True)
