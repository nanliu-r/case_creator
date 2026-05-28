import re


def parse_diff_to_changes(raw_diff: str) -> tuple[list[dict], list[dict]]:
    """Parse raw git diff into structured CPU model changes and feature changes."""
    if not raw_diff.strip():
        return [], []

    cpu_changes = _extract_cpu_model_changes(raw_diff)
    feature_changes = _extract_feature_changes(raw_diff)
    return cpu_changes, feature_changes


# Patterns for CPU model related changes
# NOTE: Use [ \t] not \s for horizontal whitespace, since \s matches \n and
# would cause false positives across diff context lines.
CPU_MODEL_PATTERNS = [
    # New CPU model definition: static X86CPUDefinition x86_cpu_xxx
    re.compile(
        r"^\+[ \t]*static[ \t]+X86CPUDefinition[ \t]+(?P<name>x86_[a-zA-Z0-9_]+)[ \t]*=",
        re.MULTILINE,
    ),
    # New CPU model registration: { .name = "xxx", ... }
    re.compile(
        r'^\+[ \t]*\{[ \t]*\.name[ \t]*=[ \t]*"(?P<name>[^"]+)"[ \t]*,',
        re.MULTILINE,
    ),
    # CPU feature flag additions: FEAT_xxx, CPUID_xxx
    re.compile(
        r"^\+[ \t]*#define[ \t]+(?P<name>(?:FEAT|CPUID|CPUID_)[A-Z0-9_]+)[ \t]+",
        re.MULTILINE,
    ),
    # New feature bit: [FEAT_xxx] = ...
    re.compile(
        r"^\+[ \t]*\[(?P<feature>FEAT_[A-Z0-9_]+)\][ \t]*=",
        re.MULTILINE,
    ),
    # CPU model version bump or alias addition
    re.compile(
        r"^\+[ \t]*\.version[ \t]*=[ \t]*(?P<version>\d+)",
        re.MULTILINE,
    ),
    # New CPU flag addition: CPUID_xxx_yyy
    re.compile(
        r"^\+[ \t]*#define[ \t]+(?P<flag>CPU_FLAG_[A-Z0-9_]+)[ \t]+",
        re.MULTILINE,
    ),
]

FEATURE_FILE_PATTERNS = re.compile(
    r"^\+\+\+\s+b/(?P<file>target/i386/[^\s]+|accel/kvm/[^\s]+|include/[^\s]*kvm[^\s]*)",
    re.MULTILINE,
)

FUNC_ADDITION_PATTERN = re.compile(
    r"^\+[ \t]*(?:static[ \t]+)?(?:inline[ \t]+)?(?P<ret_type>[a-zA-Z_][a-zA-Z0-9_*\s]+)\s+"
    r"(?P<func_name>[a-zA-Z_][a-zA-Z0-9_]+)\s*\((?P<args>[^)]*)\)\s*\{",
    re.MULTILINE,
)

MACRO_ADDITION_PATTERN = re.compile(
    r"^\+[ \t]*#define[ \t]+(?P<macro>[A-Z][A-Z0-9_]+)(?:\((?P<macro_args>[^)]*)\))?[ \t]+",
    re.MULTILINE,
)

STRUCT_ADDITION_PATTERN = re.compile(
    r"^\+[ \t]*(?:typedef[ \t]+)?struct[ \t]+(?P<struct_name>[a-zA-Z_][a-zA-Z0-9_]*)",
    re.MULTILINE,
)


def _extract_cpu_model_changes(diff: str) -> list[dict]:
    changes = []
    seen = set()

    for pattern in CPU_MODEL_PATTERNS:
        for match in pattern.finditer(diff):
            groups = match.groupdict()
            identifier = _build_identifier(groups)
            if identifier not in seen:
                seen.add(identifier)
                # Extract surrounding context (±3 lines)
                start = max(0, match.start() - 200)
                end = min(len(diff), match.end() + 200)
                context = diff[start:end]
                changes.append({
                    "type": _classify_cpu_change(groups),
                    "identifier": identifier,
                    "details": groups,
                    "context": _clean_context(context),
                })

    return changes


def _extract_feature_changes(diff: str) -> list[dict]:
    changes = []

    # Group by changed file
    files = FEATURE_FILE_PATTERNS.findall(diff)

    for file_path in set(files):
        # Extract the diff block for this file
        file_diff = _extract_file_diff_block(diff, file_path)

        # New functions
        for m in FUNC_ADDITION_PATTERN.finditer(file_diff):
            changes.append({
                "file": file_path,
                "change_type": "new_function",
                "name": m.group("func_name"),
                "signature": f"{m.group('ret_type').strip()} {m.group('func_name')}({m.group('args')})",
                "context": _clean_context(_surrounding_context(file_diff, m.start(), 300)),
            })

        # New macros
        for m in MACRO_ADDITION_PATTERN.finditer(file_diff):
            changes.append({
                "file": file_path,
                "change_type": "new_macro",
                "name": m.group("macro"),
                "definition": m.group(0).strip(),
                "context": _clean_context(_surrounding_context(file_diff, m.start(), 200)),
            })

        # New structs
        for m in STRUCT_ADDITION_PATTERN.finditer(file_diff):
            changes.append({
                "file": file_path,
                "change_type": "new_struct",
                "name": m.group("struct_name"),
                "context": _clean_context(_surrounding_context(file_diff, m.start(), 300)),
            })

    return changes


def _classify_cpu_change(groups: dict) -> str:
    """Classify the type of CPU model change."""
    if "version" in groups:
        return "version_bump"
    if "flag" in groups:
        return "new_flag"
    if "feature" in groups:
        return "new_feature_bit"
    if "name" in groups and groups["name"].startswith("x86_"):
        return "new_cpu_definition"
    if "name" in groups:
        return "new_cpu_alias"
    return "unknown"


def _build_identifier(groups: dict) -> str:
    """Build a stable identifier from named groups."""
    for key in ("name", "feature", "flag", "version"):
        if key in groups and groups[key]:
            return f"{key}:{groups[key]}"
    return "unknown"


def _clean_context(text: str) -> str:
    """Remove leading diff markers for cleaner context."""
    lines = []
    for line in text.splitlines():
        if line.startswith(("+", "-", " ")):
            lines.append(line[1:] if line[0] in "+-" else line)
        else:
            lines.append(line)
    return "\n".join(lines)


def _surrounding_context(text: str, pos: int, window: int) -> str:
    start = max(0, pos - window // 2)
    end = min(len(text), pos + window // 2)
    return text[start:end]


def _extract_file_diff_block(diff: str, file_path: str) -> str:
    """Extract the diff block for a specific file."""
    pattern = re.compile(
        rf"^diff --git a/{re.escape(file_path)}.*?(?=^diff --git|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(diff)
    return match.group(0) if match else ""
