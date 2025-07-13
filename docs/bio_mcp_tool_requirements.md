# Best Practices for Bio MCP Tool Requirements

## Overview

When developing a OpenBioMCP tool, it is essential to ensure that users can:

1. **Check** if a required tool is installed and available
2. **Install** the required tool if it is missing
3. **Update** the required tool if it is outdated
3. **Use** the tool for its intended bioinformatics functions (This can be multiple call)

This approach ensures a smooth user experience, reduces errors, and makes your MCP server robust and user-friendly.

---

## Required Tool Functions

For every external tool or dependency (e.g., FastQC, BWA, samtools), you **must** provide:

### 1. Check Requirement
- A tool to check if the requirement is installed and available in the environment.
- Should return status, version, and path if possible.

**Example:**
```python
def is_fastqc_installed(context: ModuleContext) -> dict:
    # Returns installation status, path, and version
```

### 2. Install/Update Requirement
- A tool to install (or update) the requirement if it is missing or outdated.
- Should handle platform-specific installation (For now, we care about running on MacOS and Windows).
- Should return a summary of actions taken and status.

**Example:**
```python
def install_fastqc(context: ModuleContext) -> dict:
    # Installs FastQC and returns status
```

### 3. Use the Tool
- The main tool function that performs the bioinformatics task (e.g., running FastQC on a file).
- Should check for the requirement and provide a clear error if missing.

**Example:**
```python
def fastqc(context: ModuleContext, fastq_path: str, ...) -> str:
    # Runs FastQC and returns report path
```

---

## Why Is This Required?

- **Reliability:** Users are less likely to encounter missing dependency errors.
- **Reproducibility:** Ensures all requirements are met before running analyses.
- **User Experience:** Users can easily set up and troubleshoot their environment.
- **Automation:** Enables automated workflows and pipelines to check and install requirements as needed.
- **Extensibility:** The context protocol makes it easy to add new shared information in the future.

---

## Example: FastQC in OpenBioMCP

Your FastQC feature provides:
- `is_fastqc_installed(context)` — checks if FastQC is available
- `install_fastqc(context)` — installs FastQC (and Java if needed)
- `fastqc(context, fastq_path)` — runs FastQC on a FASTQ file

This pattern should be followed for **every** external tool you integrate.

---

## Summary Table

| Function Type      | Purpose                                  | Example Name             |
|--------------------|------------------------------------------|--------------------------|
| Check requirement  | Is the tool installed/available?         | is_fastqc_installed      |
| Install/update     | Install or update the tool if missing    | install_fastqc           |
| Use the tool       | Run the tool for its main function       | fastqc                   |

---

## Final Note

**It is mandatory to provide all three: check, install/update, and use functions for every tool requirement in your Bio MCP, and to use the module context protocol for extensibility and maintainability.**

This ensures your platform is robust, user-friendly, and ready for automation and scaling. 