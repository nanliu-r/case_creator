"""Prompt templates for test case generation."""

SYSTEM_PROMPT = """You are a QA engineer specializing in qemu-kvm regression testing.
Generate comprehensive regression test cases based on CPU model changes and new feature code
between qemu-kvm versions.

Each test case must include:
1. A clear, actionable title
2. Preconditions (environment setup, VM configuration)
3. Detailed test steps
4. Expected results for each step
5. Severity and priority classification

Follow Polarion test case standards. Cover:
- Positive scenarios (new feature works as expected)
- Negative scenarios (invalid inputs, edge cases)
- Compatibility scenarios (upgrade/downgrade, live migration if applicable)
- Boundary conditions (min/max values, resource limits)

Output the test cases in JSON format as a list of objects with these keys:
- id: unique test case ID (e.g., QEMU-CPU-001)
- title: test case title
- severity: critical/high/medium/low
- priority: 1/2/3/4
- preconditions: string describing preconditions
- test_steps: list of {step: string, expected: string}
- test_type: functional/regression/compatibility/performance
- component: cpu_model/feature/kvm
"""


def build_generation_prompt(
    version_old: str,
    version_new: str,
    cpu_changes: list[dict],
    feature_changes: list[dict],
    rag_context: str,
) -> str:
    """Build the user prompt for test case generation."""
    cpu_summary = _format_changes(cpu_changes, "CPU Model Changes")
    feature_summary = _format_changes(feature_changes, "Feature Code Changes")

    rag_section = (
        f"## Relevant Knowledge Base Context\n{rag_context}"
        if rag_context
        else "## Knowledge Base\nNo relevant context found."
    )

    return f"""## Version Comparison
- Previous version: {version_old}
- New version: {version_new}

## Detected Changes

{cpu_summary}

{feature_summary}

{rag_section}

## Instructions
Based on the above changes between {version_old} and {version_new}, generate regression test cases
in JSON format. Focus on the CPU model changes and new feature code that need regression testing.

Output ONLY valid JSON array of test case objects. No other text."""


def _format_changes(changes: list[dict], title: str) -> str:
    if not changes:
        return f"### {title}\nNo changes detected."

    lines = [f"### {title} ({len(changes)} changes)"]
    for i, c in enumerate(changes, 1):
        change_type = c.get("type") or c.get("change_type", "unknown")
        identifier = c.get("identifier") or c.get("name", "unknown")
        context = c.get("context", "")[:500]
        lines.append(f"\n**Change {i}** - {change_type} | `{identifier}`")
        if c.get("file"):
            lines.append(f"- File: `{c['file']}`")
        if context:
            lines.append(f"```c\n{context}\n```")
    return "\n".join(lines)
