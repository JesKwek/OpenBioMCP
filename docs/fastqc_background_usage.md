# FastQC Background Execution and Status Checking

This document describes how to use the enhanced FastQC module that supports background execution and status checking.

## Overview

The FastQC module now supports running FastQC analysis in the background, allowing you to:
- Start FastQC jobs without blocking your application
- Check the status of running jobs
- Stop running jobs if needed
- List all active jobs
- Clean up completed jobs from memory

## New Functions

### 1. `fastqc_background()`

Runs FastQC in the background and returns job information.

**Parameters:**
- `fastq_path` (str): Full path to FASTQ file or just filename to search for
- `job_id` (str, optional): Custom job ID. If not provided, will be auto-generated
- `search_if_not_found` (bool): If True, search for the file if full path doesn't exist

**Returns:**
```python
{
    "job_id": "fastqc_sample_1234567890",
    "status": "started",
    "message": "FastQC job 'fastqc_sample_1234567890' started in background"
}
```

**Example:**
```python
from bioopenmcp.modules.fastqc.fastqc import fastqc_background

# Start FastQC in background
result = fastqc_background("sample.fastq", job_id="my_analysis_001")
print(f"Job started: {result['job_id']}")
```

### 2. `get_fastqc_status()`

Get the status of a background FastQC job.

**Parameters:**
- `job_id` (str): The job ID to check

**Returns:**
```python
{
    "job_id": "my_analysis_001",
    "fastq_path": "/path/to/sample.fastq",
    "output_dir": "/path/to/output",
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
from bioopenmcp.modules.fastqc.fastqc import get_fastqc_status

status = get_fastqc_status("my_analysis_001")
print(f"Job status: {status['status']}")
if status['status'] == 'completed':
    print(f"Report available at: {status['report_path']}")
```

### 3. `list_fastqc_jobs()`

List all background FastQC jobs and their statuses.

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
from bioopenmcp.modules.fastqc.fastqc import list_fastqc_jobs

all_jobs = list_fastqc_jobs()
print(f"Total jobs: {all_jobs['total_jobs']}")
for job_id, job_info in all_jobs['jobs'].items():
    print(f"{job_id}: {job_info['status']}")
```

### 4. `stop_fastqc_job()`

Stop a running FastQC job.

**Parameters:**
- `job_id` (str): The job ID to stop

**Returns:**
```python
{
    "job_id": "my_analysis_001",
    "status": "stopped",
    "message": "Job 'my_analysis_001' has been stopped"
}
```

**Example:**
```python
from bioopenmcp.modules.fastqc.fastqc import stop_fastqc_job

result = stop_fastqc_job("my_analysis_001")
print(f"Stop result: {result['status']}")
```

### 5. `cleanup_fastqc_jobs()`

Clean up completed or failed FastQC jobs from memory.

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
from bioopenmcp.modules.fastqc.fastqc import cleanup_fastqc_jobs

# Clean up only completed jobs
result = cleanup_fastqc_jobs(completed_only=True)
print(f"Removed {result['removed_jobs']} completed jobs")

# Clean up all jobs (including running ones)
result = cleanup_fastqc_jobs(completed_only=False)
print(f"Removed all {result['removed_jobs']} jobs")
```

## Complete Usage Example

```python
import time
from bioopenmcp.modules.fastqc.fastqc import (
    fastqc_background,
    get_fastqc_status,
    list_fastqc_jobs,
    stop_fastqc_job,
    cleanup_fastqc_jobs
)

def run_fastqc_analysis():
    # Start multiple FastQC jobs
    job1 = fastqc_background("sample1.fastq", job_id="analysis_1")
    job2 = fastqc_background("sample2.fastq", job_id="analysis_2")
    
    print(f"Started jobs: {job1['job_id']}, {job2['job_id']}")
    
    # Monitor jobs
    while True:
        status1 = get_fastqc_status("analysis_1")
        status2 = get_fastqc_status("analysis_2")
        
        print(f"Job 1: {status1['status']}, Job 2: {status2['status']}")
        
        # Check if both jobs are finished
        if status1['status'] in ['completed', 'failed'] and status2['status'] in ['completed', 'failed']:
            break
            
        time.sleep(5)  # Wait 5 seconds before next check
    
    # Get final results
    if status1['status'] == 'completed':
        print(f"Job 1 report: {status1['report_path']}")
    if status2['status'] == 'completed':
        print(f"Job 2 report: {status2['report_path']}")
    
    # Clean up
    cleanup_fastqc_jobs()

if __name__ == "__main__":
    run_fastqc_analysis()
```

## Job Status Values

- `starting`: Job is being initialized
- `running`: Job is currently executing
- `completed`: Job finished successfully
- `failed`: Job failed with an error
- `stopped`: Job was manually stopped
- `not_found`: Job ID doesn't exist

## Important Notes

1. **Memory Management**: Jobs are stored in memory. Use `cleanup_fastqc_jobs()` to remove completed jobs to prevent memory accumulation.

2. **Process Management**: Background jobs run in separate threads. The main process can continue while jobs are running.

3. **Error Handling**: Always check the `status` and `error` fields when monitoring jobs.

4. **File Paths**: The `report_path` field contains the path to the generated HTML report when the job completes successfully.

5. **Job IDs**: Job IDs must be unique. If you don't provide one, a unique ID will be generated automatically.

6. **Thread Safety**: The implementation uses a global dictionary to track jobs. In a multi-threaded environment, consider adding proper locking mechanisms if needed.

## Integration with MCP

These functions can be easily integrated into MCP tools by exposing them as tool functions. The background execution capability is particularly useful for long-running FastQC analyses that would otherwise block the MCP server. 