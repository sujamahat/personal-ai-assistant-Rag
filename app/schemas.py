from typing import List, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class Source(BaseModel):
    document: str
    chunk_index: int
    page: Optional[int] = None
    excerpt: str


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: List[Source]


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    chunks_indexed: int


class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    chunk_count: int
