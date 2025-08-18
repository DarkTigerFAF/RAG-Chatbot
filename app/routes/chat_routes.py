from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import ChatRequest
from ..rag import rag_chat
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ..database import get_db
from ..auth import SECRET_KEY, ALGORITHM
from ..models import User, History

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


@router.post("")
async def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    answer = await rag_chat(db, user.id, req.query)
    return {"answer": answer}


@router.get("/history")
def get_history(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    rows = (
        db.query(History)
        .filter(History.user_id == current_user.id)
        .order_by(History.timestamp.asc())
        .all()
    )

    history = []
    pair = {}
    for h in rows:
        if h.role == "user":
            pair = {"question": h.content, "answer": None, "created_at": h.timestamp}
        elif h.role == "assistant" and pair:
            pair["answer"] = h.content
            history.append(pair)
            pair = {}  # reset for next Q&A

    return history
