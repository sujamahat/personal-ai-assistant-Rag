from pathlib import Path
import shutil

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.rag import answer_question, ingest_document, list_documents, retrieve_context
from app.schemas import ChatRequest, ChatResponse, DocumentInfo, Source, UploadResponse
from app.store import memory


app = FastAPI(title="Personal AI Assistant with RAG")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path(settings.chroma_dir).mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/api/health")
def healthcheck() -> dict:
    return {"status": "ok"}


@app.get("/api/documents", response_model=list[DocumentInfo])
def get_documents() -> list[DocumentInfo]:
    return [DocumentInfo(**item) for item in list_documents()]


@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    target_path = Path(settings.upload_dir) / file.filename
    with target_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        result = ingest_document(target_path, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return UploadResponse(**result)


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    session_id = memory.get_or_create_session(payload.session_id or "")
    history = memory.get(session_id)

    try:
        contexts = retrieve_context(question)
        answer = answer_question(question, history, contexts)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    memory.append(session_id, "user", question)
    memory.append(session_id, "assistant", answer)

    return ChatResponse(
        session_id=session_id,
        answer=answer,
        sources=[Source(**item) for item in contexts],
    )


@app.get("/")
def serve_index() -> FileResponse:
    return FileResponse("static/index.html")
