# Background Running and Status Checking in OpenBioMCP

This document describes the comprehensive background execution and status checking capabilities implemented across the OpenBioMCP modules.

## Overview

OpenBioMCP now supports running bioinformatics tools in the background, allowing you to:
- Start long-running jobs without blocking your application
- Check the status of running jobs in real-time
- Stop running jobs if needed
- List all active jobs across different tools
- Clean up completed jobs from memory
- Monitor job progress and runtime

## Supported Modules

### 1. FastQC Module

The FastQC module provides comprehensive background execution capabilities for quality control analysis.

#### Available Functions:

- `fastqc_background()` - Run FastQC in background
- `get_fastqc_status()` - Check job status
- `list_fastqc_jobs()` - List all FastQC jobs
- `stop_fastqc_job()` - Stop a running job
- `cleanup_fastqc_jobs()` - Clean up completed jobs

#### Example Usage:

```python
from bioopenmcp.modules.fastqc.fastqc import fastqc_background, get_fastqc_status

# Start FastQC in background
job = fastqc_background("sample.fastq", job_id="qc_analysis_001")

# Check status
status = get_fastqc_status("qc_analysis_001")
print(f"Status: {status['status']}")
if status['status'] == 'completed':
    print(f"Report: {status['report_path']}")
```

### 2. Cutadapt Module

The Cutadapt module now supports background execution for adapter trimming operations.

#### Available Functions:

- `cutadapt_background()` - Run cutadapt in background
- `get_cutadapt_status()` - Check job status
- `list_cutadapt_jobs()` - List all cutadapt jobs
- `stop_cutadapt_job()` - Stop a running job
- `cleanup_cutadapt_jobs()` - Clean up completed jobs

#### Example Usage:

```python
from bioopenmcp.modules.searching_file.cutadapt.cutadapt import cutadapt_background, get_cutadapt_status

# Start cutadapt in background
job = cutadapt_background(
    args=["-a", "AGATCGGAAGAGC", "-o", "trimmed.fastq"],
    input_file="sample.fastq",
    output_file="trimmed.fastq",
    job_id="trim_001"
)

# Monitor progress
status = get_cutadapt_status("trim_001")
print(f"Command: {status['command']}")
print(f"Status: {status['status']}")
```

### 3. Trim Galore Module

The Trim Galore module now supports background execution for automated adapter and quality trimming.

#### Available Functions:

- `trim_galore_background()` - Run Trim Galore in background
- `get_trim_galore_status()` - Check job status
- `list_trim_galore_jobs()` - List all Trim Galore jobs
- `stop_trim_galore_job()` - Stop a running job
- `cleanup_trim_galore_jobs()` - Clean up completed jobs

#### Example Usage:

```python
from bioopenmcp.modules.searching_file.trim_galore.trim_galore import trim_galore_background, get_trim_galore_status

# Start Trim Galore in background
job = trim_galore_background(
    fastq_path="sample.fastq",
    extra_args="--quality 20 --length 50",
    job_id="trim_galore_001"
)

# Monitor progress
status = get_trim_galore_status("trim_galore_001")
print(f"Command: {status['command']}")
print(f"Status: {status['status']}")
if status['status'] == 'completed':
    print(f"Trimmed file: {status['trimmed_file_path']}")
```

### 4. STAR Alignment Module

The STAR alignment module now supports background execution for RNA-seq alignment.

#### Available Functions:

- `star_alignment_background()` - Run STAR alignment in background
- `get_star_status()` - Check job status
- `list_star_jobs()` - List all STAR alignment jobs
- `stop_star_job()` - Stop a running job
- `cleanup_star_jobs()` - Clean up completed jobs

#### Example Usage:

```python
from bioopenmcp.modules.star_alignment.star_alignment import star_alignment_background, get_star_status

# Start STAR alignment in background
job = star_alignment_background(
    fastq_path="sample.fastq",
    genome_dir="/path/to/genome/index",
    output_dir="/path/to/output",
    job_id="star_001",
    threads=8
)

# Monitor progress
status = get_star_status("star_001")
print(f"Command: {status['command']}")
print(f"Status: {status['status']}")
if status['status'] == 'completed':
    print(f"BAM file: {status['bam_path']}")
```

## Common Function Signatures

### Background Execution Functions

All background execution functions follow a similar pattern:

```python
def tool_background(
    # Tool-specific arguments
    job_id: Optional[str] = None,  # Auto-generated if not provided
    # ... other tool-specific parameters
) -> Dict:
    """
    Returns:
        {
            "job_id": "unique_job_id",
            "status": "started",
            "message": "Job started in background"
        }
    """
```

### Status Checking Functions

All status checking functions return consistent information:

```python
def get_tool_status(job_id: str) -> Dict:
    """
    Returns:
        {
            "job_id": "unique_job_id",
            "status": "running|completed|failed|stopped|not_found",
            "start_time": timestamp,
            "end_time": timestamp or None,
            "runtime_seconds": float or None,
            "runtime_readable": "X minutes" or None,
            "stdout": "command output",
            "stderr": "error output",
            "return_code": int or None,
            "error": "error message" or None,
            # Tool-specific fields (e.g., report_path for FastQC, trimmed_file_path for Trim Galore)
        }
    """
```

### Job Management Functions

All modules provide consistent job management:

```python
def list_tool_jobs() -> Dict:
    """List all jobs for the tool"""
    
def stop_tool_job(job_id: str) -> Dict:
    """Stop a running job"""
    
def cleanup_tool_jobs(completed_only: bool = True) -> Dict:
    """Clean up completed jobs from memory"""
```

## Job Status Values

All modules use consistent status values:

- `starting`: Job is being initialized
- `running`: Job is currently executing
- `completed`: Job finished successfully
- `failed`: Job failed with an error
- `stopped`: Job was manually stopped
- `not_found`: Job ID doesn't exist

## Complete Workflow Example

Here's a complete example showing how to use background execution for a typical bioinformatics pipeline:

```python
import time
from bioopenmcp.modules.fastqc.fastqc import fastqc_background, get_fastqc_status
from bioopenmcp.modules.searching_file.cutadapt.cutadapt import cutadapt_background, get_cutadapt_status
from bioopenmcp.modules.searching_file.trim_galore.trim_galore import trim_galore_background, get_trim_galore_status
from bioopenmcp.modules.star_alignment.star_alignment import star_alignment_background, get_star_status

def run_bioinformatics_pipeline():
    # Step 1: Quality control
    qc_job = fastqc_background("sample.fastq", job_id="qc_step")
    print(f"Started QC: {qc_job['job_id']}")
    
    # Step 2: Adapter trimming with cutadapt
    cutadapt_job = cutadapt_background(
        args=["-a", "AGATCGGAAGAGC", "-m", "20"],
        input_file="sample.fastq",
        output_file="cutadapt_trimmed.fastq",
        job_id="cutadapt_step"
    )
    print(f"Started cutadapt: {cutadapt_job['job_id']}")
    
    # Step 3: Quality trimming with Trim Galore
    trim_galore_job = trim_galore_background(
        fastq_path="sample.fastq",
        extra_args="--quality 20 --length 50",
        job_id="trim_galore_step"
    )
    print(f"Started Trim Galore: {trim_galore_job['job_id']}")
    
    # Step 4: STAR alignment
    star_job = star_alignment_background(
        fastq_path="sample.fastq",
        genome_dir="/path/to/genome/index",
        output_dir="/path/to/alignment",
        job_id="star_step",
        threads=8
    )
    print(f"Started STAR alignment: {star_job['job_id']}")
    
    # Monitor all jobs
    jobs_complete = False
    while not jobs_complete:
        qc_status = get_fastqc_status("qc_step")
        cutadapt_status = get_cutadapt_status("cutadapt_step")
        trim_galore_status = get_trim_galore_status("trim_galore_step")
        star_status = get_star_status("star_step")
        
        print(f"QC: {qc_status['status']}, Cutadapt: {cutadapt_status['status']}, Trim Galore: {trim_galore_status['status']}, STAR: {star_status['status']}")
        
        if (qc_status['status'] in ['completed', 'failed'] and 
            cutadapt_status['status'] in ['completed', 'failed'] and
            trim_galore_status['status'] in ['completed', 'failed'] and
            star_status['status'] in ['completed', 'failed']):
            jobs_complete = True
        else:
            time.sleep(30)  # Check every 30 seconds (STAR can take longer)
    
    # Get results
    if qc_status['status'] == 'completed':
        print(f"QC report: {qc_status['report_path']}")
    
    if cutadapt_status['status'] == 'completed':
        print(f"Cutadapt output: {cutadapt_status['output_file']}")
    
    if trim_galore_status['status'] == 'completed':
        print(f"Trim Galore output: {trim_galore_status['trimmed_file_path']}")
    
    if star_status['status'] == 'completed':
        print(f"STAR alignment BAM: {star_status['bam_path']}")

if __name__ == "__main__":
    run_bioinformatics_pipeline()
```

## Memory Management

### Automatic Cleanup

Jobs are stored in memory until explicitly cleaned up. Use cleanup functions to prevent memory accumulation:

```python
# Clean up only completed jobs
cleanup_fastqc_jobs(completed_only=True)
cleanup_cutadapt_jobs(completed_only=True)
cleanup_trim_galore_jobs(completed_only=True)

# Clean up all jobs (including running ones)
cleanup_fastqc_jobs(completed_only=False)
```

### Job Persistence

Job information persists for the lifetime of the MCP server process. Restarting the server will clear all job information.

## Error Handling

### Graceful Error Handling

All background functions include comprehensive error handling:

```python
try:
    job = fastqc_background("nonexistent.fastq")
except RuntimeError as e:
    print(f"Failed to start job: {e}")
```

### Status Monitoring

Always check job status and error fields:

```python
status = get_fastqc_status("job_id")
if status['status'] == 'failed':
    print(f"Job failed: {status['error']}")
```

## Performance Considerations

### Threading Model

Background jobs run in separate threads, allowing the main process to remain responsive:

- Each job runs in its own thread
- Threads are daemon threads (will terminate when main process exits)
- No blocking of the MCP server

### Resource Management

- Monitor system resources when running multiple background jobs
- Consider limiting concurrent jobs for memory-intensive tools
- Use cleanup functions to free memory from completed jobs

## Integration with MCP

All background functions are exposed as MCP tools, making them available through the MCP protocol:

```python
# In main.py
register_fastqc_tools(mcp)
register_cutadapt_tools(mcp)
register_trim_galore_tools(mcp)
register_star_alignment_tools(mcp)
```

This allows clients to:
- Start background jobs remotely
- Monitor job progress
- Retrieve results when complete
- Manage multiple concurrent analyses

## Future Enhancements

Planned enhancements for background execution:

1. **Persistent Job Storage**: Save job information to disk for persistence across server restarts
2. **Job Queuing**: Implement job queuing for resource management
3. **Progress Callbacks**: Real-time progress updates during job execution
4. **Resource Monitoring**: Automatic resource usage tracking and limits
5. **Job Dependencies**: Support for job workflows with dependencies

## Troubleshooting

### Common Issues

1. **Job not found**: Ensure job ID exists and hasn't been cleaned up
2. **Process hanging**: Use `stop_tool_job()` to terminate stuck processes
3. **Memory issues**: Regularly clean up completed jobs
4. **Tool not found**: Use installation functions to ensure tools are available

### Debugging

Enable verbose logging to debug background job issues:

```python
# Check tool installation
is_fastqc_installed()
is_cutadapt_installed()
is_trim_galore_installed()

# Check job details
status = get_fastqc_status("job_id")
print(f"Command: {status['command']}")
print(f"STDOUT: {status['stdout']}")
print(f"STDERR: {status['stderr']}")
```

## Summary

The background running and status checking functionality in OpenBioMCP provides:

- **Non-blocking execution** of long-running bioinformatics tools
- **Real-time status monitoring** of job progress
- **Consistent API** across all supported tools
- **Comprehensive error handling** and debugging information
- **Memory management** through cleanup functions
- **MCP integration** for remote job management

This enables efficient, scalable bioinformatics workflows that can handle multiple concurrent analyses while maintaining system responsiveness. 