from config import config
from rag.store import load_knowledge_base


def retrieve_context(cpu_changes: list[dict], feature_changes: list[dict]) -> str:
    """Query ChromaDB with structured change descriptions and return combined context."""
    try:
        vectorstore = load_knowledge_base()
    except Exception:
        return ""

    queries = _build_queries(cpu_changes, feature_changes)
    if not queries:
        return ""

    retrieved_docs = set()
    for query in queries:
        try:
            docs = vectorstore.similarity_search(query, k=config.rag_top_k)
            for doc in docs:
                retrieved_docs.add(doc.page_content)
        except Exception:
            continue

    return "\n\n---\n\n".join(sorted(retrieved_docs))


def _build_queries(cpu_changes: list[dict], feature_changes: list[dict]) -> list[str]:
    """Build search queries from parsed changes."""
    queries = []

    for change in cpu_changes:
        change_type = change.get("type", "unknown")
        identifier = change.get("identifier", "")
        queries.append(f"CPU model change: {change_type} - {identifier}")
        queries.append(f"regression test for CPU {identifier}")

    for change in feature_changes:
        name = change.get("name", "")
        change_type = change.get("change_type", "unknown")
        file_path = change.get("file", "")
        queries.append(f"{change_type} {name} in {file_path}")

    return queries
