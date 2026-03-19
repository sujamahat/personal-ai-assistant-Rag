from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    chat_model: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
    embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    chroma_dir: str = os.getenv("CHROMA_DIR", "./data/chroma")
    upload_dir: str = os.getenv("UPLOAD_DIR", "./data/uploads")
    top_k: int = int(os.getenv("TOP_K", "5"))
    max_history_messages: int = int(os.getenv("MAX_HISTORY_MESSAGES", "6"))


settings = Settings()
