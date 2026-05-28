"""Polarion test plan exporter (Markdown & XML formats)."""

import json
from datetime import datetime
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring


def generate_polarion_xml(test_cases: list[dict], version_old: str, version_new: str) -> str:
    """Convert test cases list to Polarion-compatible XML."""
    root = Element("testplan")
    root.set("xmlns", "http://www.polarion.com/ns/testplan")
    root.set("version", "1.0")

    # Header
    header = SubElement(root, "header")
    SubElement(header, "title").text = (
        f"QEMU-KVM Regression Test Plan: {version_old} → {version_new}"
    )
    SubElement(header, "generated").text = datetime.now().isoformat()
    SubElement(header, "source_version_old").text = version_old
    SubElement(header, "source_version_new").text = version_new
    SubElement(header, "testcase_count").text = str(len(test_cases))

    # Test cases
    cases_elem = SubElement(root, "testcases")
    for case in test_cases:
        testcase = SubElement(cases_elem, "testcase")
        testcase.set("id", case.get("id", ""))

        SubElement(testcase, "title").text = case.get("title", "")
        SubElement(testcase, "description").text = case.get("description", "")
        SubElement(testcase, "severity").text = case.get("severity", "medium")
        SubElement(testcase, "priority").text = str(case.get("priority", 3))
        SubElement(testcase, "test_type").text = case.get("test_type", "regression")
        SubElement(testcase, "component").text = case.get("component", "")
        SubElement(testcase, "preconditions").text = case.get("preconditions", "")

        # Test steps
        steps_elem = SubElement(testcase, "teststeps")
        for step in case.get("test_steps", []):
            step_elem = SubElement(steps_elem, "teststep")
            SubElement(step_elem, "step").text = step.get("step", "")
            SubElement(step_elem, "expectedresult").text = step.get("expected", "")

        # Custom fields
        cf = SubElement(testcase, "customfields")
        SubElement(cf, "customfield", {"id": "testtype", "content": case.get("test_type", "regression")})
        SubElement(cf, "customfield", {"id": "component", "content": case.get("component", "")})
        SubElement(cf, "customfield", {"id": "automation", "content": case.get("automation", "manual")})

    return _pretty_xml(root)


def generate_markdown(test_cases: list[dict], version_old: str, version_new: str) -> str:
    """Convert test cases list to Polarion-compatible Markdown format."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(test_cases)
    severity_count = _count_by_severity(test_cases)

    lines = [
        f"# QEMU-KVM Regression Test Plan: {version_old} → {version_new}",
        "",
        "## 概述",
        "",
        f"- **源版本**: {version_old}",
        f"- **目标版本**: {version_new}",
        f"- **生成时间**: {now}",
        f"- **用例总数**: {total}",
        f"- **严重程度分布**: "
        + " | ".join(f"{k}: {v}" for k, v in severity_count.items()),
        "",
        "---",
        "",
    ]

    for idx, case in enumerate(test_cases, 1):
        case_id = case.get("id", f"TC-{idx:03d}")
        lines.extend([
            f"## {idx}. [{case_id}] {case.get('title', 'Untitled')}",
            "",
            "| 属性 | 值 |",
            "|------|-----|",
            f"| **用例ID** | {case_id} |",
            f"| **严重程度** | {case.get('severity', 'medium')} |",
            f"| **优先级** | {case.get('priority', 3)} |",
            f"| **测试类型** | {case.get('test_type', 'regression')} |",
            f"| **组件** | {case.get('component', '')} |",
            "",
        ])

        desc = case.get("description", "")
        if desc:
            lines.append(f"**描述**: {desc}")
            lines.append("")

        preconditions = case.get("preconditions", "")
        if preconditions:
            lines.append("### 前置条件")
            lines.append("")
            lines.append(preconditions)
            lines.append("")

        test_steps = case.get("test_steps", [])
        if test_steps:
            lines.append("### 测试步骤")
            lines.append("")
            lines.append("| 步骤 | 预期结果 |")
            lines.append("|------|----------|")
            for step in test_steps:
                step_text = step.get("step", "").replace("|", "\\|")
                expected_text = step.get("expected", "").replace("|", "\\|")
                lines.append(f"| {step_text} | {expected_text} |")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def _count_by_severity(test_cases: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for c in test_cases:
        sev = c.get("severity", "medium")
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def parse_llm_output_to_cases(llm_output: str) -> list[dict]:
    """Parse LLM JSON output into test case list, with fallback handling."""
    text = llm_output.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove first line (```json or ```) and last line (```)
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        cases = json.loads(text)
        if isinstance(cases, list):
            return cases
        # If LLM returned a dict with a key containing the list
        if isinstance(cases, dict):
            for v in cases.values():
                if isinstance(v, list):
                    return v
        return []
    except json.JSONDecodeError:
        return _fallback_parse(text)


def _fallback_parse(text: str) -> list[dict]:
    """Best-effort parse of malformed JSON from LLM output."""
    import re
    cases = []
    # Try to extract individual JSON objects
    pattern = re.compile(r'\{[^{}]*"id"\s*:\s*"[^"]*"[^{}]*\}', re.DOTALL)
    for match in pattern.finditer(text):
        try:
            case = json.loads(match.group())
            cases.append(case)
        except json.JSONDecodeError:
            continue
    return cases


def _pretty_xml(elem: Element) -> str:
    """Pretty-print XML."""
    rough = tostring(elem, encoding="unicode")
    dom = minidom.parseString(rough)
    return dom.toprettyxml(indent="  ")
