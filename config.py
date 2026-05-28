import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # LLM
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_base_url: str = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com"))
    model_name: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "deepseek-chat"))

    # Embeddings: "local" (sentence-transformers, no API key needed) or "openai"
    embedding_provider: str = field(default_factory=lambda: os.getenv("EMBEDDING_PROVIDER", "local"))
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))

    # ChromaDB
    chroma_persist_dir: str = field(default_factory=lambda: os.getenv("CHROMA_DB_DIR", "./data/chroma_db"))
    chroma_collection: str = "qemu_knowledge"

    # RAG
    rag_top_k: int = 5

    # QEMU source files to track for CPU model changes
    qemu_cpu_files: list = field(default_factory=lambda: [
        "target/i386/cpu.c",
        "target/i386/cpu.h",
        "target/i386/kvm/kvm.c",
        "target/i386/kvm/kvm-cpu.c",
        "linux-headers/asm-x86/kvm.h",
    ])

    # Default qemu repo path
    default_repo: str = ""

    # Output
    default_output: str = "output"


config = Config()
