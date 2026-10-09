from pathlib import Path






ROOT_FOLDER = Path(r"X:\MOCKAPP\test_filesystem")







def print_tree(root: Path) -> None:
    """
    Print a recursive directory tree.

    Only names are displayed.
    File contents are NEVER opened or read.
    """

    if not root.exists():
        print(f"ERROR: Folder does not exist:\n{root}")
        return

    if not root.is_dir():
        print(f"ERROR: Path is not a directory:\n{root}")
        return

    print()
    print(root.name)
    print()

    _print_directory(root, prefix="")


def _print_directory(directory: Path, prefix: str) -> None:
    """
    Recursively print one directory level.
    """

    try:
        entries = sorted(
            directory.iterdir(),
            key=lambda path: (
                not path.is_dir(),  # folders first
                path.name.lower(),
            ),
        )

    except PermissionError:
        print(f"{prefix}└── [Permission denied]")
        return

    for index, entry in enumerate(entries):

        is_last = index == len(entries) - 1

        if is_last:
            branch = "└── "
            child_prefix = prefix + "    "
        else:
            branch = "├── "
            child_prefix = prefix + "│   "

        if entry.is_dir():

            print(f"{prefix}{branch}{entry.name}/")

            _print_directory(
                entry,
                child_prefix,
            )

        else:

            print(f"{prefix}{branch}{entry.name}")






if __name__ == "__main__":
    print_tree(ROOT_FOLDER)
