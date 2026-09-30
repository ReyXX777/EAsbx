import os
from pathlib import Path

# Folders/files to exclude from parsing
EXCLUDED_DIRS = {"__pycache__", ".venv", ".git", ".idea", ".vscode"}
EXCLUDED_FILES = {"script.py"}  # Skip itself to avoid recursive logging


def parse_project_files(root_dir: Path, output_file: Path):
    """Recursively parses all files in root_dir except excluded ones,

    writing their relative path and code contents into output_file.
    """
    total_files = 0

    with open(output_file, "w", encoding="utf-8") as out:
        out.write("==================================================\n")
        out.write("COWORK AI AGENT SUITE - PROJECT CODE BASE EXPORT\n")
        out.write("==================================================\n\n")

        for root, dirs, files in os.walk(root_dir):
            # Exclude specified directories in-place during walk
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

            for file_name in files:
                if file_name in EXCLUDED_FILES or file_name.endswith(
                    (".pyc", ".pyo", ".png", ".jpg", ".ico", ".svg")
                ):
                    continue

                full_path = Path(root) / file_name
                rel_path = full_path.relative_to(root_dir)

                out.write(f"\n{'=' * 70}\n")
                out.write(f"FILE: {rel_path}\n")
                out.write(f"{'=' * 70}\n\n")

                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        out.write(content if content.strip() else "[Empty File]")
                except Exception as e:
                    out.write(f"[Error reading file: {e}]")

                out.write("\n\n")
                total_files += 1

    print(f"✅ Parsed {total_files} files into '{output_file.name}' successfully!")


if __name__ == "__main__":
    project_root = Path(__file__).parent.resolve()
    export_output = project_root / "project_codebase_dump.txt"

    parse_project_files(project_root, export_output)
