from __future__ import annotations

import re, asyncio
from typing import Dict, List
from sqlalchemy.orm import Session

from ...models import History
from ...core.database import SessionLocal

from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents import ChatHistoryTruncationReducer
from semantic_kernel.contents import ChatMessageContent

# --------- Redaction ----------
SECRET_PAT = re.compile(
    r"(?i)(api[_-]?key|secret|token|password|bearer)\s*[:=]\s*([A-Za-z0-9._\-]{10,})"
)


def redact(text: str) -> str:
    return SECRET_PAT.sub(lambda m: f"{m.group(1)}: ***REDACTED***", text or "")


# --------- Cache ----------
MAX_TURN = 8
_CACHED_HISTORY: Dict[int, ChatHistoryTruncationReducer] = {}

SYSTEM_MESSAGE = """
You are a RAG assistant.

Policy:
- Answer questions strictly based on retrieved chunks [#n] and recent chat history.
- COMPENSATE for potential typos by matching intended meaning to retrieved content.
- For multi-part questions: answer supported parts with [#n]; for unsupported parts: "Insufficient context for: <part>."
- If chunks are partially relevant, answer only what's present and note limits.
- Do NOT fabricate or use outside knowledge.
- Each factual statement must cite at least one [#n].
- When compensating typos, say: "Assuming you meant '<term>' based on context".
- ALWAYS output retrieved chunks as they are; do not alter wording.
- Never mention "retrieved chunks" explicitly to the user.

Output:
- Concise answers grounded only in the retrieved context.
- If context is limited, state so before answering the supported part.
"""


class ChatHistoryService:
    async def build_context(self, db: Session, user_id: int, limit: int = MAX_TURN):
        ch = _CACHED_HISTORY.get(user_id)
        if ch:
            return ch

        reducer = ChatHistoryTruncationReducer(
            target_count=limit, threshold_count=6, auto_reduce=True
        )
        await reducer.add_message_async(
            ChatMessageContent(role=AuthorRole.SYSTEM, content=SYSTEM_MESSAGE)
        )

        rows: List[History] = (
            db.query(History)
            .filter(History.user_id == user_id)
            .order_by(History.timestamp.desc())
            .limit(limit)
            .all()
        )
        rows.reverse()

        for r in rows:
            await reducer.add_message_async(
                ChatMessageContent(
                    role=AuthorRole.USER, content=redact(r.question or "")
                )
            )
            await reducer.add_message_async(
                ChatMessageContent(
                    role=AuthorRole.ASSISTANT, content=redact(r.answer or "")
                )
            )

        _CACHED_HISTORY[user_id] = reducer
        return reducer

    async def persist_pair(self, user_id: int, question: str, answer: str) -> None:
        def _write(session: Session, uid: int, q: str, a: str) -> None:
            try:
                session.add(History(user_id=uid, question=q, answer=a))
                session.commit()
            finally:
                session.close()

        session = SessionLocal()
        await asyncio.to_thread(_write, session, user_id, question, answer)

        ch = _CACHED_HISTORY.get(user_id)
        if ch:
            await ch.add_message_async(
                ChatMessageContent(role=AuthorRole.USER, content=redact(question or ""))
            )
            await ch.add_message_async(
                ChatMessageContent(
                    role=AuthorRole.ASSISTANT, content=redact(answer or "")
                )
            )
