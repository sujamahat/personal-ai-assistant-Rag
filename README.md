# Personal AI Assistant with RAG

This is a personal AI assistant that chats over my own documents instead of answering from the internet alone. I built it to understand the full RAG loop myself: upload, parse, chunk, embed, retrieve, answer, and show sources.

The app lets me upload PDFs, Markdown files, and text notes, stores document chunks in ChromaDB, and then uses OpenAI embeddings plus the Responses API to answer questions with grounded context.

Live demo: [personal-ai-assistant-rag-production.up.railway.app](https://personal-ai-assistant-rag-production.up.railway.app)

## What It Does

- Upload `.pdf`, `.txt`, and `.md` files
- Extract and chunk document text
- Store embeddings in a local Chroma vector database
- Retrieve the most relevant chunks for each question
- Answer with source-aware responses
- Keep short conversation memory for follow-up questions

## Tech Stack

- FastAPI
- OpenAI Responses API
- `text-embedding-3-small`
- ChromaDB
- PyPDF
- HTML, CSS, and vanilla JavaScript
- Railway for deployment

## Engineering Challenges

- Getting chunk size and overlap to feel useful without flooding the model with repetitive context
- Making the answers sound grounded instead of generic by forcing the assistant to stay close to retrieved text
- Handling PDFs and plain text with one simple ingestion flow
- Keeping the project small enough to understand end to end while still feeling like a real product

## What I Learned

- Retrieval quality matters as much as the model choice
- Small product decisions like showing sources make the app feel much more trustworthy
- A simple RAG app has a lot of moving parts, but each one becomes manageable when built step by step
- Deploying an AI app is not just about the model; config, storage, and environment variables matter just as much

## Running Locally

```bash
cd /Users/sujam/projects/personal-ai-assistant-rag
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add your OpenAI API key to `.env`, then run:

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Deployment

This project is set up for Railway with a Dockerfile-based deploy. The same FastAPI app serves both the API and the frontend, so there is only one service to deploy.

Required Railway variables:

- `OPENAI_API_KEY`
- `OPENAI_CHAT_MODEL`
- `OPENAI_EMBEDDING_MODEL`
- `TOP_K`
- `MAX_HISTORY_MESSAGES`

## API

- `GET /api/health`
- `GET /api/documents`
- `POST /api/upload`
- `POST /api/chat`

## Next Improvements

- Persist chat sessions in SQLite
- Add document deletion
- Add better PDF parsing for messy files
- Add a lightweight evaluation set for retrieval quality
