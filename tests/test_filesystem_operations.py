from pathlib import Path

from filesystem.filesystem_models import FilesystemOperation, OperationType
from filesystem.filesystem_operations import FilesystemOperations
from filesystem.filesystem_sandbox import SandboxValidator


def make_ops(tmp_path: Path):
    root = tmp_path / "sandbox"
    root.mkdir()
    return root, FilesystemOperations(SandboxValidator(root))


def test_list_and_read(tmp_path):
    root, ops = make_ops(tmp_path)
    (root / "notes").mkdir()
    (root / "notes" / "hello.txt").write_text("hello", encoding="utf-8")

    listed = ops.dispatch(
        FilesystemOperation(OperationType.LIST_DIRECTORY, path="notes")
    )
    assert listed.success
    assert listed.data[0].name == "hello.txt"

    read = ops.dispatch(
        FilesystemOperation(OperationType.READ_FILE, path="notes/hello.txt")
    )
    assert read.success
    assert read.data == "hello"


def test_write_and_delete(tmp_path):
    root, ops = make_ops(tmp_path)

    written = ops.dispatch(
        FilesystemOperation(
            OperationType.WRITE_FILE,
            path="project/a.txt",
            content="abc",
        )
    )
    assert written.success
    assert (root / "project" / "a.txt").read_text() == "abc"

    deleted = ops.dispatch(
        FilesystemOperation(OperationType.DELETE_FILE, path="project/a.txt")
    )
    assert deleted.success
    assert not (root / "project" / "a.txt").exists()


def test_calculator_does_not_execute_code(tmp_path):
    _, ops = make_ops(tmp_path)

    result = ops.dispatch(
        FilesystemOperation(
            OperationType.CALCULATE,
            expression="2 * (3 + 4)",
        )
    )
    assert result.success
    assert result.data == 14

    blocked = ops.dispatch(
        FilesystemOperation(
            OperationType.CALCULATE,
            expression="__import__('os').system('whoami')",
        )
    )
    assert not blocked.success
