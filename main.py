#!/usr/bin/env python3
"""QEMU-KVM Case Creator — Generate regression test cases from version diffs.

Usage:
    python main.py --init-rag
    python main.py --old v10.1.0 --new v10.2.0
    python main.py --changelog diff.txt --old 8.1.0 --new 8.2.0
"""

import argparse
import sys
import os
from datetime import datetime

from config import config
from graph.workflow import build_workflow


def _make_output_paths(output_dir: str) -> tuple[str, str]:
    """Generate timestamped output paths.

    Returns (md_path, json_path).
    """
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(output_dir, exist_ok=True)
    filename = f"testplan_{run_id}"
    md_path = os.path.join(output_dir, filename + ".md")
    json_path = os.path.join(output_dir, filename + ".json")
    return md_path, json_path


def cmd_init_rag(docs_dir: str):
    """Initialize the RAG knowledge base from markdown documents."""
    from rag.store import build_knowledge_base
    build_knowledge_base(docs_dir)
    print("RAG knowledge base initialized successfully.")


def cmd_generate(
    repo_path: str,
    changelog_file: str,
    version_old: str,
    version_new: str,
    output: str,
):
    """Run the full test case generation workflow."""
    if not version_old or not version_new:
        print("Error: --old and --new versions are required.")
        sys.exit(1)

    if not config.openai_api_key:
        print("Error: OPENAI_API_KEY is required. Set it in .env or environment.")
        sys.exit(1)

    raw_diff = ""
    if changelog_file:
        from analyzer.differ import read_changelog_file
        raw_diff = read_changelog_file(changelog_file)
        print(f"Loaded changelog from {changelog_file} ({len(raw_diff)} chars)")
    else:
        if not repo_path:
            repo_path = config.default_repo
        print(f"Using repo: {repo_path} ({version_old} → {version_new})")

    initial_state = {
        "repo_path": repo_path or "",
        "version_old": version_old,
        "version_new": version_new,
        "raw_diff": raw_diff,
        "cpu_changes": [],
        "feature_changes": [],
        "rag_context": "",
        "test_cases": [],
        "polarion_xml": "",
        "error": "",
    }

    workflow = build_workflow()
    print("Running workflow...")

    config_dict = {"configurable": {"thread_id": "case-creator-session"}}
    final_state = workflow.invoke(initial_state, config_dict)

    if final_state.get("error"):
        print(f"Workflow error: {final_state['error']}")
        sys.exit(1)

    cpu_count = len(final_state.get("cpu_changes", []))
    feat_count = len(final_state.get("feature_changes", []))
    case_count = len(final_state.get("test_cases", []))
    print(f"Detected {cpu_count} CPU model changes, {feat_count} feature changes.")
    print(f"Generated {case_count} test cases.")

    md_path, json_path = _make_output_paths(output)
    output_md = final_state.get("polarion_xml", "")
    if output_md:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(output_md)
        print(f"Test plan exported to {md_path}")

    import json
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(final_state.get("test_cases", []), f, indent=2, ensure_ascii=False)
    print(f"Raw test cases exported to {json_path}")


def main():
    parser = argparse.ArgumentParser(
        description="QEMU-KVM Case Creator — Generate regression test cases in Markdown format."
    )
    parser.add_argument("--init-rag", action="store_true",
                        help="Initialize the RAG knowledge base from data/qemu_knowledge/")
    parser.add_argument("--docs-dir", default="./data/qemu_knowledge",
                        help="Directory with markdown docs for RAG (default: ./data/qemu_knowledge)")
    parser.add_argument("--repo", default="",
                        help="Path to local qemu git repository")
    parser.add_argument("--changelog", default="",
                        help="Path to a pre-generated diff/changelog file")
    parser.add_argument("--old", default="",
                        help="Previous qemu-kvm version tag (e.g. v8.1.0)")
    parser.add_argument("--new", default="",
                        help="New qemu-kvm version tag (e.g. v8.2.0)")
    parser.add_argument("--output", default=config.default_output,
                        help="Output directory (default: output/)")

    args = parser.parse_args()

    if args.init_rag:
        cmd_init_rag(args.docs_dir)
    else:
        cmd_generate(args.repo, args.changelog, args.old, args.new, args.output)


if __name__ == "__main__":
    main()
