# Cowork Filesystem Agent

This package implements the sandboxed filesystem layer for MOCKAPP.

## Root boundary

Create one dedicated test root, for example:

```text
X:\MOCKAPP\test_filesystem
```

Initialize it with:

```python
from filesystem.filesystem_service import SandboxFilesystemService

service = SandboxFilesystemService(r"X:\MOCKAPP\test_filesystem")
```

All tool paths are sandbox-relative:

```python
service.read_file("project_alpha/notes/readme.md")
```

The service rejects:

```text
C:\Windows\...
..\outside.txt
../../outside.txt
\\server\share\...
```

It also resolves symlinks/junction-like path components before allowing access.

## Architecture

```text
FilesystemAgent
      |
      v
FilesystemOperation
      |
      v
SandboxFilesystemService
      |
      +--> SandboxValidator
      |
      +--> FilesystemOperations
                 |
                 +--> list_directory
                 +--> search_files
                 +--> read_file
                 +--> read_table
                 +--> calculate
                 +--> write_file
                 +--> append_file
                 +--> create_directory
                 +--> delete_file
                 +--> delete_directory
                 +--> move
                 +--> copy
```

The agent never performs direct `Path.read_*`, `open()`, `unlink()`, etc.

## Approval boundary

This package deliberately does **not** silently bypass the existing approval system.

The intended orchestration is:

1. Gemini classifies the user's task.
2. The dispatcher identifies `FILESYSTEM_TASK`.
3. Read/search operations may execute directly under sandbox validation.
4. Modify/delete operations are sent through the existing `ApprovalEngine`.
5. Only after approval does the dispatcher execute those structured operations.
6. `FilesystemAgent` remains unaware of Qt approval UI.

## Browser integration

`FilesWorkspace` is a normal `QWidget` and can later be assigned to the existing:

```python
BrowserWindowWidget.files_workspace
```

No changes to `browser_window.py` are required to install this package.
