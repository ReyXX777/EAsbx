from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

FILES_TO_EXPORT = [
    "task_graph.py",
    "agent_state_manager.py",
    "agent_engine.py",
    "main.py",
]


OUTPUT_FILE = "selected_code_export.txt"


# ============================================================
# CODE
# ============================================================

def read_file(file_path: Path) -> str:
    """Read a source file and return its contents."""
    return file_path.read_text(encoding="utf-8")


def build_export(project_root: Path, files: list[str]) -> str:
    """Build a single text export containing filenames and source code."""

    output_parts = []

    output_parts.append("=" * 80)
    output_parts.append("COWORK AI AGENT SUITE - SELECTED CODE EXPORT")
    output_parts.append("=" * 80)
    output_parts.append("")

    for filename in files:
        file_path = project_root / filename

        output_parts.append("")
        output_parts.append("=" * 80)
        output_parts.append(f"FILE: {filename}")
        output_parts.append("=" * 80)
        output_parts.append("")

        if not file_path.exists():
            output_parts.append(
                f"[ERROR] File not found: {file_path}"
            )
            output_parts.append("")
            continue

        if not file_path.is_file():
            output_parts.append(
                f"[ERROR] Path is not a file: {file_path}"
            )
            output_parts.append("")
            continue

        try:
            content = read_file(file_path)
            output_parts.append(content)

        except UnicodeDecodeError:
            output_parts.append(
                "[ERROR] Could not decode file as UTF-8."
            )

        except Exception as exc:
            output_parts.append(
                f"[ERROR] Could not read file: {exc}"
            )

        output_parts.append("")

    return "\n".join(output_parts)


def main():
    """Generate the selected source-code export."""

    # The directory containing this script is treated as project root.
    project_root = Path(__file__).resolve().parent

    output_path = project_root / OUTPUT_FILE

    export_content = build_export(
        project_root,
        FILES_TO_EXPORT,
    )

    # Overwrite the previous export on every run.
    output_path.write_text(
        export_content,
        encoding="utf-8",
    )

    print()
    print("=" * 60)
    print("CODE EXPORT COMPLETE")
    print("=" * 60)
    print(f"Project root : {project_root}")
    print(f"Output file  : {output_path}")
    print()
    print("Files included:")

    for filename in FILES_TO_EXPORT:
        print(f"  - {filename}")

    print()
    print("The previous export was overwritten.")
    print("=" * 60)


if __name__ == "__main__":
    main()