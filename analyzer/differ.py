import subprocess
import os
from config import config


def run_git_diff(repo_path: str, version_old: str, version_new: str) -> str:
    """Run git diff between two version tags on tracked CPU files."""
    if not os.path.isdir(repo_path):
        raise ValueError(f"Repo path does not exist: {repo_path}")

    file_patterns = config.qemu_cpu_files
    diff_parts = []

    for pattern in file_patterns:
        try:
            result = subprocess.run(
                ["git", "diff", f"{version_old}..{version_new}", "--", pattern],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0 and result.stdout.strip():
                diff_parts.append(result.stdout)
            if result.stderr:
                print(f"[warn] git diff stderr for {pattern}: {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            print(f"[warn] git diff timed out for {pattern}")
        except FileNotFoundError:
            raise RuntimeError("git not found. Ensure git is installed and in PATH.")

    return "\n".join(diff_parts)


def read_changelog_file(filepath: str) -> str:
    """Read diff/changelog content from a text file."""
    if not os.path.isfile(filepath):
        raise ValueError(f"Changelog file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()
