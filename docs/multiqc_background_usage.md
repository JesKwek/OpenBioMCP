# MultiQC Background Execution and Status Checking

This document describes how to use the MultiQC module that supports background execution and status checking.

## Overview

The MultiQC module supports running MultiQC analysis in the background, allowing you to:
- Start MultiQC jobs without blocking your application
- Check the status of running jobs
- Stop running jobs if needed
- List all active jobs
- Clean up completed jobs from memory

MultiQC is a tool that aggregates results from bioinformatics analyses across many samples into a single report. It can process outputs from FastQC, STAR, cutadapt, Trim Galore, and many other bioinformatics tools.

## New Functions

### 1. `multiqc()`

Runs MultiQC on a directory containing bioinformatics analysis results.

**Parameters:**
- `input_dir` (str): Directory containing analysis results to aggregate
- `output_dir` (str, optional): Output directory for MultiQC report (defaults to input_dir/multiqc_report)
- `config_file` (str, optional): Optional MultiQC configuration file
- `extra_args` (str): Additional command-line arguments for MultiQC

**Returns:**
- Path to the MultiQC HTML report

**Example:**
```python
from bioopenmcp.modules.multiqc.multiqc import multiqc

# Run MultiQC on a directory containing FastQC results
report_path = multiqc("/path/to/analysis_results")
print(f"MultiQC report generated: {report_path}")
```

### 2. `multiqc_background()`

Runs MultiQC in the background and returns job information.

**Parameters:**
- `input_dir` (str): Directory containing analysis results to aggregate
- `output_dir` (str, optional): Output directory for MultiQC report
- `config_file` (str, optional): Optional MultiQC configuration file
- `extra_args` (str): Additional command-line arguments for MultiQC
- `job_id` (str, optional): Custom job ID. If not provided, will be auto-generated

**Returns:**
```python
{
    "job_id": "multiqc_results_1234567890",
    "status": "started",
    "message": "MultiQC job 'multiqc_results_1234567890' started in background"
}
```

**Example:**
```python
from bioopenmcp.modules.multiqc.multiqc import multiqc_background

# Start MultiQC in background
result = multiqc_background(
    "/path/to/analysis_results", 
    output_dir="/path/to/reports",
    job_id="my_multiqc_001"
)
print(f"Job started: {result['job_id']}")
```

### 3. `get_multiqc_status()`

Get the status of a background MultiQC job.

**Parameters:**
- `job_id` (str): The job ID to check

**Returns:**
```python
{
    "job_id": "my_multiqc_001",
    "input_dir": "/path/to/analysis_results",
    "output_dir": "/path/to/reports",
    "config_file": None,
    "extra_args": "",
    "status": "running",  # or "completed", "failed", "stopped", "not_found"
    "start_time": 1234567890.123,
    "end_time": None,  # or timestamp when finished
    "runtime_seconds": None,  # calculated if job is finished
    "stdout": "",
    "stderr": "",
    "return_code": None,
    "report_path": None,  # path to HTML report if completed
    "error": None  # error message if failed
}
```

**Example:**
```python
from bioopenmcp.modules.multiqc.multiqc import get_multiqc_status

status = get_multiqc_status("my_multiqc_001")
print(f"Job status: {status['status']}")
if status['status'] == 'completed':
    print(f"Report available at: {status['report_path']}")
```

### 4. `list_multiqc_jobs()`

List all background MultiQC jobs and their statuses.

**Returns:**
```python
{
    "total_jobs": 2,
    "jobs": {
        "job_001": {
            "job_id": "job_001",
            "status": "running",
            # ... other job info
        },
        "job_002": {
            "job_id": "job_002", 
            "status": "completed",
            # ... other job info
        }
    }
}
```

**Example:**
```python
from bioopenmcp.modules.multiqc.multiqc import list_multiqc_jobs

all_jobs = list_multiqc_jobs()
print(f"Total jobs: {all_jobs['total_jobs']}")
for job_id, job_info in all_jobs['jobs'].items():
    print(f"{job_id}: {job_info['status']}")
```

### 5. `stop_multiqc_job()`

Stop a running MultiQC job.

**Parameters:**
- `job_id` (str): The job ID to stop

**Returns:**
```python
{
    "job_id": "my_multiqc_001",
    "status": "stopped",
    "message": "Job 'my_multiqc_001' has been stopped"
}
```

**Example:**
```python
from bioopenmcp.modules.multiqc.multiqc import stop_multiqc_job

result = stop_multiqc_job("my_multiqc_001")
print(f"Stop result: {result['status']}")
```

### 6. `cleanup_multiqc_jobs()`

Clean up completed or failed MultiQC jobs from memory.

**Parameters:**
- `completed_only` (bool): If True, only remove completed/failed jobs. If False, remove all jobs.

**Returns:**
```python
{
    "removed_jobs": 3,
    "remaining_jobs": 1,
    "removed_job_ids": ["job_001", "job_002", "job_003"]
}
```

**Example:**
```python
from bioopenmcp.modules.multiqc.multiqc import cleanup_multiqc_jobs

# Clean up only completed jobs
result = cleanup_multiqc_jobs(completed_only=True)
print(f"Removed {result['removed_jobs']} completed jobs")

# Clean up all jobs (including running ones)
result = cleanup_multiqc_jobs(completed_only=False)
print(f"Removed all {result['removed_jobs']} jobs")
```

### 7. `install_multiqc()`

Install MultiQC if not present. Tries multiple installation methods to handle various system configurations.

**Installation Methods (in order of preference):**
1. **pipx** - Recommended for Python applications (isolated environment)
2. **pipx via brew** - Install pipx using Homebrew, then install MultiQC via pipx
3. **pip --user** - User-local installation (avoids system conflicts)
4. **pip** - System-wide installation (may fail on externally-managed environments)

**Note:** MultiQC is not available in Homebrew (including brewsci/bio tap). It's only available via PyPI.

**Returns:**
```python
{
    "multiqc_installed": True,
    "multiqc_install_attempted": False,
    "multiqc_install_output": None,
    "python_available": True,
    "pip_available": True,
    "pipx_available": True,
    "brew_available": True,
    "installation_method": "pipx",  # Which method succeeded
    "error": None,
    "suggestions": []  # Helpful suggestions if installation fails
}
```

**Example Success Response:**
```python
{
    "multiqc_installed": True,
    "multiqc_install_attempted": True,
    "multiqc_install_output": "pipx install attempt: Successfully installed multiqc-1.15",
    "python_available": True,
    "pip_available": True,
    "pipx_available": True,
    "brew_available": True,
    "installation_method": "pipx",
    "error": None,
    "suggestions": []
}
```

**Example Failure Response (externally-managed-environment):**
```python
{
    "multiqc_installed": False,
    "multiqc_install_attempted": True,
    "multiqc_install_output": "pip install attempt: error: externally-managed-environment...",
    "python_available": True,
    "pip_available": True,
    "pipx_available": False,
    "brew_available": True,
    "installation_method": None,
    "error": "All installation methods failed. See suggestions for manual installation options.",
    "suggestions": [
        "Install pipx via brew: brew install pipx && pipx install multiqc",
        "Create virtual environment: python3 -m venv multiqc_env && source multiqc_env/bin/activate && pip install multiqc",
        "Use --break-system-packages (not recommended): pip install multiqc --break-system-packages"
    ]
}
```

### 8. `is_multiqc_installed()`

Check if MultiQC is installed on the system.

**Returns:**
```python
{
    "multiqc_installed": True,
    "multiqc_path": "/usr/local/bin/multiqc",
    "multiqc_version": "MultiQC v1.15",
    "which_output": "/usr/local/bin/multiqc",
    "python_available": True,
    "python_path": "/usr/bin/python3",
    "python_version": "Python 3.9.7",
    "pip_available": True,
    "pip_path": "/usr/bin/pip3",
    "error": None
}
```

## Complete Usage Example

```python
import time
from bioopenmcp.modules.multiqc.multiqc import (
    multiqc_background,
    get_multiqc_status,
    list_multiqc_jobs,
    stop_multiqc_job,
    cleanup_multiqc_jobs
)

def run_multiqc_analysis():
    # Start MultiQC job on a directory containing FastQC and STAR results
    job = multiqc_background(
        "/path/to/analysis_results", 
        output_dir="/path/to/multiqc_reports",
        job_id="comprehensive_analysis"
    )
    
    print(f"Started MultiQC job: {job['job_id']}")
    
    # Monitor job
    while True:
        status = get_multiqc_status("comprehensive_analysis")
        
        print(f"Job status: {status['status']}")
        
        # Check if job is finished
        if status['status'] in ['completed', 'failed', 'stopped']:
            break
            
        time.sleep(10)  # Wait 10 seconds before next check
    
    # Get final results
    if status['status'] == 'completed':
        print(f"MultiQC report: {status['report_path']}")
        print(f"Runtime: {status.get('runtime_readable', 'Unknown')}")
    elif status['status'] == 'failed':
        print(f"Job failed: {status.get('error', 'Unknown error')}")
    
    # Clean up
    cleanup_multiqc_jobs()

if __name__ == "__main__":
    run_multiqc_analysis()
```

## Typical MultiQC Workflow

```python
# 1. Run quality control and analysis tools
fastqc_background("sample1.fastq", job_id="qc_sample1")
fastqc_background("sample2.fastq", job_id="qc_sample2")
star_alignment_background("sample1.fastq", "/path/to/genome", "/path/to/output", job_id="align_sample1")
star_alignment_background("sample2.fastq", "/path/to/genome", "/path/to/output", job_id="align_sample2")

# 2. Wait for all jobs to complete (implementation depends on your needs)
# ... monitoring code ...

# 3. Run MultiQC to aggregate all results
multiqc_background("/path/to/all_results", job_id="final_report")
```

## Job Status Values

- `starting`: Job is being initialized
- `running`: Job is currently executing
- `completed`: Job finished successfully
- `failed`: Job failed with an error
- `stopped`: Job was manually stopped
- `not_found`: Job ID doesn't exist

## Supported Input Types

MultiQC can process results from many bioinformatics tools, including:

- **FastQC**: Quality control reports for sequencing data
- **STAR**: RNA-seq alignment logs and statistics
- **cutadapt**: Adapter trimming logs
- **Trim Galore**: Quality and adapter trimming reports
- **Bowtie2**: Alignment statistics
- **samtools**: BAM/SAM file statistics
- **Picard**: Various metrics from Picard tools
- **GATK**: Variant calling metrics
- **And many more...**

## Configuration

MultiQC can be customized using configuration files. Create a YAML configuration file and pass it via the `config_file` parameter:

```yaml
# multiqc_config.yaml
title: "My Project Analysis"
subtitle: "Quality control and alignment results"

report_comment: >
    This report contains quality control metrics and alignment statistics
    for our RNA-seq experiment.

extra_fn_clean_exts:
    - .fastq
    - .fq
    - .bam
    - .sam

module_order:
    - fastqc
    - star
    - cutadapt
```

## Important Notes

1. **Memory Management**: Jobs are stored in memory. Use `cleanup_multiqc_jobs()` to remove completed jobs.

2. **Input Directory**: MultiQC recursively searches the input directory for supported file types.

3. **Output Files**: MultiQC generates an HTML report (`multiqc_report.html`) and a data directory with raw data.

4. **Performance**: MultiQC is generally fast, but processing many large files can take time.

5. **Dependencies**: MultiQC requires Python and is installed via pip.

6. **File Detection**: MultiQC automatically detects file types based on content and naming patterns.

## Handling Installation Issues

### Externally-Managed Environment (PEP 668)

Modern Python installations (especially on macOS with Homebrew) may prevent direct pip installations to avoid conflicts. The `install_multiqc()` function handles this automatically by trying multiple methods:

```python
from bioopenmcp.modules.multiqc.multiqc import install_multiqc

result = install_multiqc()

if result["multiqc_installed"]:
    print(f"MultiQC installed successfully using: {result['installation_method']}")
else:
    print(f"Installation failed: {result['error']}")
    print("Suggestions:")
    for suggestion in result["suggestions"]:
        print(f"  - {suggestion}")
```

### Manual Installation Options

If automatic installation fails, try these manual methods:

**1. Using pipx (Recommended):**
```bash
brew install pipx  # Install pipx first
pipx install multiqc
```

**2. Using Homebrew + pipx (macOS):**
```bash
# MultiQC is not in Homebrew, but we can install pipx via brew
brew install pipx
pipx install multiqc
```

**3. Using Virtual Environment:**
```bash
python3 -m venv multiqc_env
source multiqc_env/bin/activate
pip install multiqc
```

**4. User Installation:**
```bash
pip install --user multiqc
```

**5. System Installation (if you know what you're doing):**
```bash
pip install multiqc --break-system-packages
```

### Troubleshooting

- **Command not found after installation**: The installation directory may not be in your PATH. Check `~/.local/bin` for user installations or pipx's bin directory.
- **Permission errors**: Try user installation (`--user` flag) or use pipx.
- **Version conflicts**: Use virtual environments or pipx to isolate installations.

## Integration with MCP

These functions are automatically registered as MCP tools when the module is imported, making them available for use in MCP-based applications. The background execution capability is particularly useful for processing large datasets without blocking the MCP server.
