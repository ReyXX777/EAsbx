from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

# Every path here is relative to the MOCKAPP project root.
#
# You can specify files at ANY directory depth.
#
# Examples:
#
#   "main.py"
#   "approval/models.py"
#   "approval/approval_widget.py"
#   "schemas/approval_schema.json"
#   "agents/filesystem/filesystem_agent.py"
#
# Both "/" and "\" are accepted on Windows.

FILES_TO_EXPORT = [
    "filesystem/tools/__init__.py",
    "filesystem/tools/tool_models.py",
    "filesystem/tools/tool_registry.py",
    "filesystem/tools/tool_dispatcher.py",
    "filesystem/tools/filesystem_tools.py",
    "filesystem/tools/compute_tools.py",
]


OUTPUT_FILE = "selected_code_export.txt"


# ============================================================
# PATH HELPERS
# ============================================================


def normalize_relative_path(file_path: str) -> Path:
    """
    Convert a user-supplied relative path into a Path.

    Both Windows-style and Unix-style separators are accepted.

    Examples:
        approval/models.py
        approval\\models.py

    Both become the same relative project path.
    """

    normalized = file_path.replace("\\", "/")

    return Path(*normalized.split("/"))


def resolve_project_file(
    project_root: Path,
    relative_path: str,
) -> Path:
    """
    Resolve a file relative to the project root.

    This function also prevents accidental paths from escaping
    the project directory.
    """

    relative = normalize_relative_path(relative_path)

    file_path = (project_root / relative).resolve()
    project_root = project_root.resolve()

    try:
        file_path.relative_to(project_root)
    except ValueError:
        raise ValueError(f"Path escapes project root: {relative_path}")

    return file_path


# ============================================================
# FILE READING
# ============================================================


def read_file(file_path: Path) -> str:
    """
    Read a source file and return its contents.
    """

    return file_path.read_text(
        encoding="utf-8",
    )


# ============================================================
# EXPORT BUILDER
# ============================================================


def build_export(
    project_root: Path,
    files: list[str],
) -> str:
    """
    Build a single text export containing:

        - relative filename
        - absolute source path
        - source code
        - errors, if any
    """

    output_parts = []

    output_parts.append("=" * 80)
    output_parts.append("COWORK AI AGENT SUITE - SELECTED CODE EXPORT")
    output_parts.append("=" * 80)
    output_parts.append("")
    output_parts.append(f"PROJECT ROOT: {project_root}")
    output_parts.append("")
    output_parts.append(f"TOTAL FILES REQUESTED: {len(files)}")
    output_parts.append("")

    for relative_filename in files:

        output_parts.append("")
        output_parts.append("=" * 80)
        output_parts.append(f"FILE: {relative_filename}")
        output_parts.append("=" * 80)
        output_parts.append("")

        # ----------------------------------------------------
        # Resolve relative path safely
        # ----------------------------------------------------

        try:
            file_path = resolve_project_file(
                project_root,
                relative_filename,
            )

        except Exception as exc:
            output_parts.append(f"[ERROR] Could not resolve path: {exc}")
            output_parts.append("")
            continue

        # ----------------------------------------------------
        # Verify file exists
        # ----------------------------------------------------

        if not file_path.exists():
            output_parts.append(f"[ERROR] File not found:")
            output_parts.append(f"        {file_path}")
            output_parts.append("")
            continue

        # ----------------------------------------------------
        # Verify it is actually a file
        # ----------------------------------------------------

        if not file_path.is_file():
            output_parts.append(f"[ERROR] Path is not a file:")
            output_parts.append(f"        {file_path}")
            output_parts.append("")
            continue

        # ----------------------------------------------------
        # Read file
        # ----------------------------------------------------

        try:
            content = read_file(file_path)

            output_parts.append(content)

        except UnicodeDecodeError:
            output_parts.append("[ERROR] Could not decode file as UTF-8.")

        except Exception as exc:
            output_parts.append(f"[ERROR] Could not read file: {exc}")

        output_parts.append("")

    return "\n".join(output_parts)


# ============================================================
# MAIN
# ============================================================


def main():
    """
    Generate the selected source-code export.
    """

    # --------------------------------------------------------
    # The directory containing this script is the project root.
    # --------------------------------------------------------

    project_root = Path(__file__).resolve().parent

    output_path = project_root / OUTPUT_FILE

    # --------------------------------------------------------
    # Build export
    # --------------------------------------------------------

    export_content = build_export(
        project_root,
        FILES_TO_EXPORT,
    )

    # --------------------------------------------------------
    # Overwrite previous export
    # --------------------------------------------------------

    output_path.write_text(
        export_content,
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # Console summary
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("CODE EXPORT COMPLETE")
    print("=" * 60)

    print(f"Project root : {project_root}")
    print(f"Output file  : {output_path}")
    print()

    print("Files requested:")

    for filename in FILES_TO_EXPORT:
        print(f"  - {filename}")

    print()
    print(f"Total files: {len(FILES_TO_EXPORT)}")

    print()
    print("The previous export was overwritten.")

    print("=" * 60)


if __name__ == "__main__":
    main()
