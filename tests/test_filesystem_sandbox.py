from pathlib import Path

import pytest

from filesystem.filesystem_sandbox import SandboxValidator, SandboxViolation


def test_relative_file_is_contained(tmp_path: Path):
    root = tmp_path / "sandbox"
    root.mkdir()
    (root / "notes").mkdir()

    validator = SandboxValidator(root)
    assert validator.resolve("notes/test.txt", allow_missing=True).parent == root / "notes"


@pytest.mark.parametrize(
    "path",
    [
        "../outside.txt",
        "../../outside.txt",
        r"..\outside.txt",
        r"C:\Windows\System32",
        r"X:\MOCKAPP\..\outside.txt",
        r"\\server\share\file.txt",
        "/etc/passwd",
    ],
)
def test_escape_attempts_are_rejected(tmp_path: Path, path: str):
    root = tmp_path / "sandbox"
    root.mkdir()

    validator = SandboxValidator(root)

    with pytest.raises(SandboxViolation):
        validator.resolve(path, allow_missing=True)


def test_symlink_escape_is_rejected(tmp_path: Path):
    root = tmp_path / "sandbox"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()

    link = root / "link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation is unavailable on this environment.")

    validator = SandboxValidator(root)

    with pytest.raises(SandboxViolation):
        validator.resolve("link/secret.txt", allow_missing=True)
