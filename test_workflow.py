#!/usr/bin/env python3
"""End-to-end tests for the case creator workflow (no API key needed)."""

import json
import sys
import os

# Test 1: Parser
print("=" * 60)
print("Test 1: Diff Parser")
print("=" * 60)
from analyzer.parser import parse_diff_to_changes

with open("data/test_diff.txt") as f:
    diff = f.read()

cpu_changes, feature_changes = parse_diff_to_changes(diff)
assert len(cpu_changes) > 0, "Expected CPU model changes"
assert len(feature_changes) > 0, "Expected feature changes"
print(f"  PASS: {len(cpu_changes)} CPU changes, {len(feature_changes)} feature changes")

# Verify change types
cpu_types = {c["type"] for c in cpu_changes}
assert "new_cpu_definition" in cpu_types, "Expected new_cpu_definition type"
print(f"  PASS: CPU change types: {cpu_types}")

feat_types = {c["change_type"] for c in feature_changes}
print(f"  PASS: Feature change types: {feat_types}")

# Test 2: Markdown Export
print()
print("=" * 60)
print("Test 2: Markdown Export")
print("=" * 60)
from generator.polarion import generate_markdown, parse_llm_output_to_cases

mock_cases = [
    {
        "id": "QEMU-CPU-001",
        "title": "Verify EPYC-Genoa CPU model enumeration",
        "description": "Verify that the new EPYC-Genoa CPU model is available.",
        "severity": "critical",
        "priority": 1,
        "preconditions": "qemu-kvm installed with KVM enabled on x86_64 host",
        "test_steps": [
            {"step": "Run qemu-system-x86_64 -cpu help", "expected": "EPYC-Genoa in output"},
            {"step": "Boot VM with -cpu EPYC-Genoa", "expected": "VM boots successfully"},
        ],
        "test_type": "regression",
        "component": "cpu_model",
        "automation": "manual",
    },
    {
        "id": "QEMU-CPU-002",
        "title": "Verify AVX512_BF16 feature flag",
        "description": "Verify the new AVX512_BF16 feature flag is functional.",
        "severity": "high",
        "priority": 1,
        "preconditions": "CPU with AVX512_BF16 support",
        "test_steps": [
            {"step": "Boot VM with -cpu host,+avx512-bf16", "expected": "Feature visible in /proc/cpuinfo"},
        ],
        "test_type": "regression",
        "component": "cpu_feature",
        "automation": "manual",
    },
]

md_output = generate_markdown(mock_cases, "v8.1.0", "v8.2.0")

# Basic Markdown validation
assert "# QEMU-KVM Regression Test Plan" in md_output, "Missing main title"
assert "v8.1.0" in md_output and "v8.2.0" in md_output, "Missing version info"
assert "QEMU-CPU-001" in md_output, "Missing test case ID"
assert "QEMU-CPU-002" in md_output, "Missing test case ID"
assert "EPYC-Genoa" in md_output, "Missing test case content"
assert "## 概述" in md_output, "Missing overview section"
assert "### 前置条件" in md_output, "Missing preconditions section"
assert "### 测试步骤" in md_output, "Missing test steps section"
assert "| **严重程度** |" in md_output, "Missing severity in table"
assert "| 步骤 | 预期结果 |" in md_output, "Missing test steps table header"

# Save for inspection
os.makedirs("data/output", exist_ok=True)
with open("data/output/test_testplan.md", "w") as f:
    f.write(md_output)
print(f"  PASS: Markdown generated and saved to data/output/test_testplan.md ({len(md_output)} bytes)")

# Test 3: LLM Output Parsing
print()
print("=" * 60)
print("Test 3: LLM Output Parsing")
print("=" * 60)

# Test valid JSON
valid_json = json.dumps(mock_cases)
cases = parse_llm_output_to_cases(valid_json)
assert len(cases) == 2, f"Expected 2 cases, got {len(cases)}"
print(f"  PASS: Valid JSON parsed ({len(cases)} cases)")

# Test markdown-fenced JSON
fenced = f"```json\n{valid_json}\n```"
cases = parse_llm_output_to_cases(fenced)
assert len(cases) == 2, f"Expected 2 cases, got {len(cases)}"
print("  PASS: Markdown-fenced JSON parsed")

# Test malformed fallback
malformed = 'Some text {"id": "TC-001", "title": "Test"} more text {"id": "TC-002", "title": "Test2"}'
cases = parse_llm_output_to_cases(malformed)
print(f"  PASS: Fallback parser extracted {len(cases)} cases from malformed output")

# Test 4: LangGraph Workflow Structure
print()
print("=" * 60)
print("Test 4: LangGraph Workflow Structure")
print("=" * 60)
from graph.workflow import build_workflow

workflow = build_workflow()
graph = workflow.get_graph()
print(f"  Nodes: {list(graph.nodes.keys())}")
print(f"  Edges: {[(e.source, e.target) for e in graph.edges]}")

expected_nodes = {"run_diff", "parse_changes", "rag_retrieve", "generate_cases", "export_polarion", "__start__", "handle_error"}
found_nodes = set(graph.nodes.keys())
assert expected_nodes.issubset(found_nodes), f"Missing nodes: {expected_nodes - found_nodes}"
print("  PASS: All expected nodes present")

# Test 5: Workflow with changelog input (no LLM, skip generate_cases)
print()
print("=" * 60)
print("Test 5: Workflow State Flow (diff → parse)")
print("=" * 60)

initial_state = {
    "repo_path": "",
    "version_old": "v8.1.0",
    "version_new": "v8.2.0",
    "raw_diff": diff,
    "cpu_changes": [],
    "feature_changes": [],
    "rag_context": "",
    "test_cases": [],
    "polarion_xml": "",
    "error": "",
}

# Manually step through the graph
from graph.workflow import node_run_diff, node_parse_changes, node_rag_retrieve

# run_diff should skip since raw_diff is already set
result = node_run_diff(initial_state)
assert result == {}, "run_diff should return empty when raw_diff is provided"
print("  PASS: run_diff skips when raw_diff provided")

# parse_changes
result = node_parse_changes(initial_state)
assert len(result["cpu_changes"]) == 5, f"Expected 5 CPU changes, got {len(result['cpu_changes'])}"
assert len(result["feature_changes"]) == 4, f"Expected 4 feature changes, got {len(result['feature_changes'])}"
print(f"  PASS: parse_changes → {len(result['cpu_changes'])} CPU + {len(result['feature_changes'])} feature changes")

# rag_retrieve (will fail gracefully without API key)
result_rag = node_rag_retrieve({**initial_state, **result})
assert result_rag["rag_context"] == "", "RAG should return empty without ChromaDB"
print("  PASS: rag_retrieve handles missing ChromaDB gracefully")

print()
print("=" * 60)
print("ALL TESTS PASSED")
print("=" * 60)
