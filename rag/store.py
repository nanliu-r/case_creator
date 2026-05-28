import os
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import config
from rag.embeddings import get_embeddings


def build_knowledge_base(docs_dir: str = "./data/qemu_knowledge") -> Chroma:
    """Load markdown documents from docs_dir and index into ChromaDB."""
    if not os.path.isdir(docs_dir):
        raise ValueError(f"Documents directory not found: {docs_dir}")

    loader = DirectoryLoader(
        docs_dir,
        glob="**/*.md",
        loader_cls=TextLoader,
        show_progress=True,
    )
    documents = loader.load()

    if not documents:
        raise ValueError(f"No .md documents found in {docs_dir}")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n## ", "\n### ", "\n#### ", "\n", " ", ""],
    )
    chunks = text_splitter.split_documents(documents)

    embeddings = get_embeddings()

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=config.chroma_persist_dir,
        collection_name=config.chroma_collection,
    )

    print(f"Indexed {len(chunks)} chunks from {len(documents)} documents into ChromaDB.")
    return vectorstore


def load_knowledge_base() -> Chroma:
    """Load the existing ChromaDB vector store."""
    if not os.path.isdir(config.chroma_persist_dir):
        raise RuntimeError(
            f"ChromaDB not found at {config.chroma_persist_dir}. Run --init-rag first."
        )

    embeddings = get_embeddings()
    return Chroma(
        persist_directory=config.chroma_persist_dir,
        embedding_function=embeddings,
        collection_name=config.chroma_collection,
    )
