from __future__ import annotations

import re
from typing import Dict, List

from sqlalchemy.orm import Session
from ...models import History
from semantic_kernel.contents import ChatHistory


SECRET_PAT = re.compile(
    r"(?i)(api[_-]?key|secret|token|password|bearer)\s*[:=]\s*([A-Za-z0-9._\-]{10,})"
)


def redact(text: str) -> str:
    return SECRET_PAT.sub(lambda m: f"{m.group(1)}: ***REDACTED***", text or "")


_CACHED_HISTORY: Dict[int, ChatHistory] = {}

MAX_TURN = 8


def _trim_chat_history(ch: ChatHistory, max_turn: int = MAX_TURN) -> ChatHistory:
    sys_msgs = [m for m in ch.messages if getattr(m, "role", "") == "system"]
    non_sys = [m for m in ch.messages if getattr(m, "role", "") != "system"]

    tail = non_sys[-max_turn:]

    new_ch = ChatHistory()
    if sys_msgs:
        new_ch.add_system_message(sys_msgs[0].content)
    for m in tail:
        if m.role == "user":
            new_ch.add_user_message(m.content)
        elif m.role == "assistant":
            new_ch.add_assistant_message(m.content)
        else:
            # fallback if other roles exist
            new_ch.add_assistant_message(m.content)
    return new_ch


class ChatHistoryService:
    async def build_context(
        self, db: Session, user_id: int, limit: int = MAX_TURN
    ) -> ChatHistory:
        if user_id in _CACHED_HISTORY:
            _CACHED_HISTORY[user_id] = _trim_chat_history(_CACHED_HISTORY[user_id])
            return _CACHED_HISTORY[user_id]

        msgs: List[History] = (
            db.query(History)
            .filter(History.user_id == user_id)
            .order_by(History.timestamp.desc())
            .limit(limit)
            .all()
        )
        msgs.reverse()

        system_message = """You are a RAG assistant.

                        Policy:
                        - Answer ONLY using retrieved chunks [#n] and recent chat history.
                        - If a question has multiple parts, treat each part separately:
                        • If a part is supported by retrieved chunks, answer it and CITE [#n].
                        • If a part is NOT supported, reply: "Insufficient context for: <that part>."
                        - Every factual sentence MUST include at least one [#n] citation.
                        - Do not use outside knowledge. Do not mention tools.

                        Output:
                        - Concise answer. No preambles. Include [#n] after each claim.
                        """

        chat_history = ChatHistory()
        chat_history.add_system_message(system_message)
        for m in msgs:
            chat_history.add_user_message(redact(m.question or ""))
            chat_history.add_assistant_message(redact(m.answer or ""))

        chat_history = _trim_chat_history(chat_history)

        _CACHED_HISTORY[user_id] = chat_history
        return chat_history

    async def persist_pair(
        self, db: Session, user_id: int, question: str, answer: str
    ) -> None:
        db.add(History(user_id=user_id, question=question, answer=answer))
        db.commit()

        if user_id in _CACHED_HISTORY:
            ch = _CACHED_HISTORY[user_id]
            ch.add_user_message(redact(question))
            ch.add_assistant_message(redact(answer))
            _CACHED_HISTORY[user_id] = _trim_chat_history(ch)
