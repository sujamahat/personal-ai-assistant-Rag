from typing import Dict, List
from uuid import uuid4

import chromadb

from app.config import settings


class ChatMemory:
    def __init__(self) -> None:
        self._sessions: Dict[str, List[dict]] = {}

    def get_or_create_session(self, session_id: str = "") -> str:
        if session_id and session_id in self._sessions:
            return session_id
        new_id = session_id or str(uuid4())
        self._sessions.setdefault(new_id, [])
        return new_id

    def append(self, session_id: str, role: str, content: str) -> None:
        history = self._sessions.setdefault(session_id, [])
        history.append({"role": role, "content": content})
        self._sessions[session_id] = history[-settings.max_history_messages :]

    def get(self, session_id: str) -> List[dict]:
        return self._sessions.get(session_id, [])


memory = ChatMemory()
client = chromadb.PersistentClient(path=settings.chroma_dir)
collection = client.get_or_create_collection(name="personal_assistant_docs")
