"""LangGraph workflow orchestration for the case creator."""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from graph.state import WorkflowState
from analyzer.differ import run_git_diff, read_changelog_file
from analyzer.parser import parse_diff_to_changes
from rag.retriever import retrieve_context
from generator.prompts import SYSTEM_PROMPT, build_generation_prompt
from generator.polarion import generate_markdown, parse_llm_output_to_cases


def node_run_diff(state: WorkflowState) -> dict:
    """Run git diff between two versions, or load from file."""
    repo_path = state.get("repo_path", "")
    version_old = state["version_old"]
    version_new = state["version_new"]

    if state.get("raw_diff"):
        return {}

    if not repo_path:
        return {"error": "repo_path is required when raw_diff is not provided"}

    try:
        raw_diff = run_git_diff(repo_path, version_old, version_new)
        return {"raw_diff": raw_diff}
    except Exception as e:
        return {"error": str(e)}


def node_parse_changes(state: WorkflowState) -> dict:
    """Parse raw diff into structured CPU model and feature changes."""
    raw_diff = state["raw_diff"]
    cpu_changes, feature_changes = parse_diff_to_changes(raw_diff)
    return {
        "cpu_changes": cpu_changes,
        "feature_changes": feature_changes,
    }


def node_rag_retrieve(state: WorkflowState) -> dict:
    """Use RAG to retrieve relevant context for detected changes."""
    cpu_changes = state.get("cpu_changes", [])
    feature_changes = state.get("feature_changes", [])

    try:
        rag_context = retrieve_context(cpu_changes, feature_changes)
        return {"rag_context": rag_context}
    except Exception:
        # ChromaDB not initialized or API key missing; skip RAG
        return {"rag_context": ""}


def node_generate_cases(state: WorkflowState) -> dict:
    """Generate test cases using LLM with prompts enriched by RAG context."""
    from langchain_openai import ChatOpenAI
    from config import config

    prompt = build_generation_prompt(
        state["version_old"],
        state["version_new"],
        state.get("cpu_changes", []),
        state.get("feature_changes", []),
        state.get("rag_context", ""),
    )

    llm_kwargs = {
        "model": config.model_name,
        "api_key": config.openai_api_key,
        "temperature": 0.2,
    }
    if config.openai_base_url:
        llm_kwargs["base_url"] = config.openai_base_url

    llm = ChatOpenAI(**llm_kwargs)
    response = llm.invoke(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
    )

    test_cases = parse_llm_output_to_cases(response.content)
    return {"test_cases": test_cases}


def node_export_polarion(state: WorkflowState) -> dict:
    """Export test cases to Markdown format."""
    output = generate_markdown(
        state["test_cases"],
        state["version_old"],
        state["version_new"],
    )
    return {"polarion_xml": output}


def node_handle_error(state: WorkflowState) -> dict:
    """Error terminal node."""
    return {}


def build_workflow() -> StateGraph:
    """Build and compile the LangGraph workflow."""
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("run_diff", node_run_diff)
    workflow.add_node("parse_changes", node_parse_changes)
    workflow.add_node("rag_retrieve", node_rag_retrieve)
    workflow.add_node("generate_cases", node_generate_cases)
    workflow.add_node("export_polarion", node_export_polarion)
    workflow.add_node("handle_error", node_handle_error)

    # Set entry point
    workflow.set_entry_point("run_diff")

    # Edges
    workflow.add_conditional_edges(
        "run_diff",
        lambda s: "handle_error" if s.get("error") else "parse_changes",
        {"parse_changes": "parse_changes", "handle_error": "handle_error"},
    )
    workflow.add_edge("parse_changes", "rag_retrieve")
    workflow.add_edge("rag_retrieve", "generate_cases")
    workflow.add_edge("generate_cases", "export_polarion")
    workflow.add_edge("export_polarion", END)
    workflow.add_edge("handle_error", END)

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)
