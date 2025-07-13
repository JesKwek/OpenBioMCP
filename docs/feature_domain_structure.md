# Organizing by Feature/Domain in OpenBioMCP

## Overview

Organizing your codebase by feature or domain means grouping related logic, tools, and resources into their own subdirectories or modules. This approach makes your project more modular, scalable, and easier to maintain as it grows.

---

## Directory Structure Example

Suppose you have features like FastQC, Alignment, and Reporting. Your structure could look like this:

```
modules/
  fastqc/
    fastqc.py         # All FastQC-related tools and logic
    __init__.py       # Exposes the public API and tool registration
  alignment/
    alignment.py      # Alignment-related tools and logic
    __init__.py
  reporting/
    reporting.py      # Reporting tools and logic
    __init__.py
```

Each feature/domain gets its own folder and module(s).

---

## Inside Each Feature Module

For example, in `modules/fastqc/fastqc.py`:
```python
def find_fastq_files(...): ...
def fastqc(...): ...
def install_fastqc(...): ...
def is_fastqc_installed(...): ...
```

In `modules/alignment/alignment.py`:
```python
def run_alignment(...): ...
def check_alignment_status(...): ...
```

---

## Exposing a Public API and Tool Registration with `__init__.py`

Each feature's `__init__.py` should expose the public API and provide a registration function for MCP tools. For example, in `modules/fastqc/__init__.py`:

```python
from .fastqc import (
    find_fastq_files,
    fastqc,
    install_fastqc,
    is_fastqc_installed,
)

def register_fastqc_tools(mcp):
    mcp.tool()(find_fastq_files)
    mcp.tool()(fastqc)
    mcp.tool()(install_fastqc)
    mcp.tool()(is_fastqc_installed)
```

---

## Import and Register in main.py

In your `main.py`, you can now import and register all FastQC tools with a single call:

```python
from modules.fastqc import register_fastqc_tools

# Register all FastQC tools
register_fastqc_tools(mcp)
```

This keeps `main.py` clean and makes it easy to add new features.

---

## Benefits

- **Separation of concerns:** Each feature is self-contained.
- **Scalability:** Add new features without cluttering existing files.
- **Team collaboration:** Multiple people can work on different features without merge conflicts.
- **Testing:** Easier to test and maintain.
- **Clean imports and registration:** Thanks to the `__init__.py` pattern.

---

## Adding a New Feature Example

If you want to add a new feature, e.g., “Trimming”:
- Create `modules/trimming/trimming.py` for your logic
- Create `modules/trimming/__init__.py` to expose the public API and registration function
- Import and register in `main.py`:
  ```python
  from modules.trimming import register_trimming_tools
  register_trimming_tools(mcp)
  ```

---

## Summary Table

| Structure                | Example Path                        | Contents                        |
|--------------------------|-------------------------------------|---------------------------------|
| FastQC feature           | modules/fastqc/fastqc.py            | FastQC tools, logic             |
| FastQC API/registration  | modules/fastqc/__init__.py          | Public API, tool registration   |
| Alignment feature        | modules/alignment/alignment.py      | Alignment tools, logic          |
| Alignment API/registration| modules/alignment/__init__.py      | Public API, tool registration   |
| Reporting feature        | modules/reporting/reporting.py      | Reporting tools, logic          |
| Reporting API/registration| modules/reporting/__init__.py      | Public API, tool registration   |

---

## Why Organize by Feature/Domain?

- Keeps related code together
- Makes it easy to find and update features
- Reduces merge conflicts
- Supports project growth and team scaling
- Enables clean, scalable tool registration for MCP 