from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages


class WorkflowState(TypedDict):
    repo_path: str
    version_old: str
    version_new: str
    raw_diff: str
    cpu_changes: list[dict]
    feature_changes: list[dict]
    rag_context: str
    test_cases: list[dict]
    polarion_xml: str
    error: str
