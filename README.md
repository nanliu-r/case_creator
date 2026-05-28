# QEMU-KVM Case Creator

LangGraph-based test case generation system that automatically creates regression test plans from QEMU-KVM version diffs, powered by RAG (Retrieval-Augmented Generation) and LLM.

## How It Works

```
 ┌──────────┐     ┌───────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐
 │ Git Diff │ ──> │ Parse Changes │ ──> │ RAG Retrieve │ ──> │ Generate     │ ──> │ Export      │
 │ (vA→vB)  │     │ (CPU/Feature) │     │ (ChromaDB)   │     │ (LLM)        │     │ (Markdown)  │
 └──────────┘     └───────────────┘     └──────────────┘     └──────────────┘     └─────────────┘
```

1. **Diff** — Extracts code changes between two QEMU version tags via `git diff`
2. **Parse** — Identifies CPU model changes and feature changes from the diff
3. **RAG** — Retrieves relevant knowledge from ChromaDB (QEMU documentation, test patterns)
4. **Generate** — Uses the LLM to generate structured test cases with RAG-enriched context
5. **Export** — Outputs test plans in Markdown format (compatible with Polarion)

## Setup

### Prerequisites

- Python 3.10+
- DeepSeek API key (or any OpenAI-compatible endpoint)

### Install

```bash
cd case_creator
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
# Edit .env with your API key
```

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | DeepSeek API key (required) |
| `OPENAI_BASE_URL` | API endpoint, defaults to `https://api.deepseek.com` |
| `MODEL_NAME` | Model name, defaults to `deepseek-chat` |
| `EMBEDDING_PROVIDER` | `local` (free) or `openai` |
| `CHROMA_DB_DIR` | ChromaDB storage path |

## Usage

### 1. Initialize the RAG knowledge base (first time only)

```bash
python main.py --init-rag
```

This indexes the markdown documents in `data/qemu_knowledge/` into ChromaDB.

### 2. Generate test cases

Using a local QEMU repository:

```bash
python main.py --repo /path/to/qemu --old v8.1.0 --new v8.2.0
```

Using a pre-generated diff file:

```bash
python main.py --changelog diff.txt --old v8.1.0 --new v8.2.0
```

Output is written to `output/` with timestamped filenames:
- `testplan_*.md` — Markdown test plan
- `testplan_*.json` — Raw JSON test cases

## Project Structure

```
case_creator/
├── main.py              # CLI entry point
├── config.py            # Configuration (env vars, paths)
├── analyzer/
│   ├── differ.py        # Git diff extraction
│   └── parser.py        # Diff parsing (CPU/feature changes)
├── rag/
│   ├── embeddings.py    # Embedding model (local/OpenAI)
│   ├── store.py         # ChromaDB knowledge base builder
│   └── retriever.py     # Context retrieval
├── generator/
│   ├── prompts.py       # LLM prompt templates
│   └── polarion.py      # Output formatting & parsing
├── graph/
│   ├── state.py         # LangGraph workflow state
│   └── workflow.py      # Workflow graph definition
├── data/
│   └── qemu_knowledge/  # RAG source documents
└── output/              # Generated test plans
```

## Tech Stack

- [LangGraph](https://github.com/langchain-ai/langgraph) — Workflow orchestration
- [LangChain](https://github.com/langchain-ai/langchain) — LLM abstraction
- [ChromaDB](https://github.com/chroma-core/chroma) — Vector store for RAG
- [DeepSeek](https://deepseek.com) — LLM via OpenAI-compatible API
