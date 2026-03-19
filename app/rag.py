from pathlib import Path
from typing import Dict, List
from uuid import uuid4

from openai import OpenAI, OpenAIError, RateLimitError
from pypdf import PdfReader

from app.chunking import chunk_text
from app.config import settings
from app.store import collection


openai_client = OpenAI(api_key=settings.openai_api_key)


def _extract_text(file_path: Path) -> List[Dict[str, object]]:
    suffix = file_path.suffix.lower()
    if suffix in {".txt", ".md"}:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        return [{"page": None, "text": text}]

    if suffix == ".pdf":
        reader = PdfReader(str(file_path))
        pages = []
        for page_number, page in enumerate(reader.pages, start=1):
            pages.append({"page": page_number, "text": page.extract_text() or ""})
        return pages

    raise ValueError(f"Unsupported file type: {suffix}")


def _embed_texts(texts: List[str]) -> List[List[float]]:
    try:
        response = openai_client.embeddings.create(
            model=settings.embedding_model,
            input=texts,
        )
    except RateLimitError as exc:
        raise ValueError(
            "OpenAI quota is unavailable for embeddings right now. Check your billing and API usage, then try again."
        ) from exc
    except OpenAIError as exc:
        raise ValueError(f"OpenAI embeddings request failed: {exc}") from exc

    return [item.embedding for item in response.data]


def ingest_document(file_path: Path, original_filename: str) -> Dict[str, object]:
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is missing. Add it to your environment before uploading.")

    extracted_sections = _extract_text(file_path)
    payloads = []
    metadatas = []
    ids = []

    document_id = str(uuid4())
    for section in extracted_sections:
        chunks = chunk_text(str(section["text"]))
        for chunk_index, chunk in enumerate(chunks):
            payloads.append(chunk)
            metadatas.append(
                {
                    "document_id": document_id,
                    "filename": original_filename,
                    "page": int(section["page"]) if section["page"] is not None else -1,
                    "chunk_index": chunk_index,
                }
            )
            ids.append(f"{document_id}:{section['page']}:{chunk_index}")

    if not payloads:
        raise ValueError("No extractable text was found in that file.")

    embeddings = _embed_texts(payloads)
    collection.add(
        ids=ids,
        documents=payloads,
        metadatas=metadatas,
        embeddings=embeddings,
    )

    return {
        "document_id": document_id,
        "filename": original_filename,
        "chunks_indexed": len(payloads),
    }


def list_documents() -> List[Dict[str, object]]:
    stored = collection.get(include=["metadatas"])
    counts: Dict[str, Dict[str, object]] = {}
    for metadata in stored.get("metadatas", []):
        if not metadata:
            continue
        document_id = str(metadata["document_id"])
        if document_id not in counts:
            counts[document_id] = {
                "document_id": document_id,
                "filename": metadata["filename"],
                "chunk_count": 0,
            }
        counts[document_id]["chunk_count"] += 1
    return list(counts.values())


def retrieve_context(question: str) -> List[Dict[str, object]]:
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is missing. Add it to your environment before chatting.")

    query_embedding = _embed_texts([question])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=settings.top_k,
        include=["documents", "metadatas", "distances"],
    )

    contexts = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    for document, metadata in zip(documents, metadatas):
        page = None if metadata["page"] == -1 else int(metadata["page"])
        contexts.append(
            {
                "document": metadata["filename"],
                "chunk_index": int(metadata["chunk_index"]),
                "page": page,
                "excerpt": document,
            }
        )
    return contexts


def answer_question(question: str, history: List[dict], contexts: List[Dict[str, object]]) -> str:
    if not contexts:
        return "I could not find relevant context in the uploaded documents yet. Try uploading files first."

    history_text = "\n".join(
        f"{item['role'].upper()}: {item['content']}" for item in history[-settings.max_history_messages :]
    )
    context_text = "\n\n".join(
        (
            f"[Source {index + 1}] Document: {context['document']} | "
            f"Page: {context['page'] if context['page'] is not None else 'N/A'} | "
            f"Chunk: {context['chunk_index']}\n{context['excerpt']}"
        )
        for index, context in enumerate(contexts)
    )
    prompt = (
        "Use only the retrieved context to answer the user's question. "
        "If the context is incomplete, say what is missing. "
        "End with a brief 'Sources used' line mentioning the source numbers.\n\n"
        f"Conversation history:\n{history_text or 'No previous messages.'}\n\n"
        f"Retrieved context:\n{context_text}\n\n"
        f"User question:\n{question}"
    )

    try:
        response = openai_client.responses.create(
            model=settings.chat_model,
            instructions="You are a personal AI assistant that answers with grounded, citation-aware responses.",
            input=prompt,
        )
    except RateLimitError as exc:
        raise ValueError(
            "OpenAI quota is unavailable for answer generation right now. Check your billing and API usage, then try again."
        ) from exc
    except OpenAIError as exc:
        raise ValueError(f"OpenAI response generation failed: {exc}") from exc

    return response.output_text.strip()
