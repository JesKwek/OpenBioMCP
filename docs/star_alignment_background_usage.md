# STAR Alignment Background Execution and Status Checking

This document describes how to use the enhanced STAR alignment module that supports background execution and status checking.

## Overview

The STAR alignment module now supports running STAR RNA-seq alignment in the background, allowing you to:
- Start STAR alignment jobs without blocking your application
- Check the status of running jobs
- Stop running jobs if needed
- List all active jobs
- Clean up completed jobs from memory

## New Functions

### 1. `star_alignment_background()`

Runs STAR alignment in the background and returns job information.

**Parameters:**
- `fastq_path` (str): Full path to FASTQ file or just filename to search for
- `genome_dir` (str): Path to the STAR genome directory
- `output_dir` (str): Directory to write STAR output
- `job_id` (str, optional): Custom job ID. If not provided, will be auto-generated
- `search_if_not_found` (bool): If True, search for the file if full path doesn't exist
- `threads` (int): Number of threads to use for STAR alignment (default: 4)

**Returns:**
```python
{
    "job_id": "star_sample_1234567890",
    "status": "started",
    "message": "STAR alignment job 'star_sample_1234567890' started in background"
}
```

**Example:**
```python
from bioopenmcp.modules.star_alignment.star_alignment import star_alignment_background

# Start STAR alignment in background
result = star_alignment_background(
    fastq_path="sample.fastq",
    genome_dir="/path/to/genome/index",
    output_dir="/path/to/output",
    job_id="my_alignment_001",
    threads=8
)
print(f"Job started: {result['job_id']}")
```

### 2. `get_star_status()`

Get the status of a background STAR alignment job.

**Parameters:**
- `job_id` (str): The job ID to check

**Returns:**
```python
{
    "job_id": "my_alignment_001",
    "fastq_path": "/path/to/sample.fastq",
    "genome_dir": "/path/to/genome/index",
    "output_dir": "/path/to/output",
    "out_prefix": "/path/to/output/star_",
    "command": "STAR --genomeDir /path/to/genome/index --readFilesIn /path/to/sample.fastq ...",
    "status": "running",  # or "completed", "failed", "stopped", "not_found"
    "start_time": 1234567890.123,
    "end_time": None,  # or timestamp when finished
    "runtime_seconds": None,  # calculated if job is finished
    "stdout": "",
    "stderr": "",
    "return_code": None,
    "bam_path": None,  # path to BAM file if completed
    "error": None  # error message if failed
}
```

**Example:**
```python
from bioopenmcp.modules.star_alignment.star_alignment import get_star_status

status = get_star_status("my_alignment_001")
print(f"Job status: {status['status']}")
if status['status'] == 'completed':
    print(f"BAM file available at: {status['bam_path']}")
```

### 3. `list_star_jobs()`

List all background STAR alignment jobs and their statuses.

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
from bioopenmcp.modules.star_alignment.star_alignment import list_star_jobs

all_jobs = list_star_jobs()
print(f"Total jobs: {all_jobs['total_jobs']}")
for job_id, job_info in all_jobs['jobs'].items():
    print(f"{job_id}: {job_info['status']}")
```

### 4. `stop_star_job()`

Stop a running STAR alignment job.

**Parameters:**
- `job_id` (str): The job ID to stop

**Returns:**
```python
{
    "job_id": "my_alignment_001",
    "status": "stopped",
    "message": "Job 'my_alignment_001' has been stopped"
}
```

**Example:**
```python
from bioopenmcp.modules.star_alignment.star_alignment import stop_star_job

result = stop_star_job("my_alignment_001")
print(f"Stop result: {result['status']}")
```

### 5. `cleanup_star_jobs()`

Clean up completed or failed STAR alignment jobs from memory.

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
from bioopenmcp.modules.star_alignment.star_alignment import cleanup_star_jobs

# Clean up only completed jobs
result = cleanup_star_jobs(completed_only=True)
print(f"Removed {result['removed_jobs']} completed jobs")

# Clean up all jobs (including running ones)
result = cleanup_star_jobs(completed_only=False)
print(f"Removed all {result['removed_jobs']} jobs")
```

## Complete Usage Example

```python
import time
from bioopenmcp.modules.star_alignment.star_alignment import (
    star_alignment_background,
    get_star_status,
    list_star_jobs,
    stop_star_job,
    cleanup_star_jobs
)

def run_star_analysis():
    # Start multiple STAR alignment jobs
    job1 = star_alignment_background(
        fastq_path="sample1.fastq",
        genome_dir="/path/to/genome/index",
        output_dir="/path/to/output1",
        job_id="alignment_1",
        threads=8
    )
    
    job2 = star_alignment_background(
        fastq_path="sample2.fastq",
        genome_dir="/path/to/genome/index",
        output_dir="/path/to/output2",
        job_id="alignment_2",
        threads=8
    )
    
    print(f"Started jobs: {job1['job_id']}, {job2['job_id']}")
    
    # Monitor jobs
    while True:
        status1 = get_star_status("alignment_1")
        status2 = get_star_status("alignment_2")
        
        print(f"Job 1: {status1['status']}, Job 2: {status2['status']}")
        
        # Check if both jobs are finished
        if status1['status'] in ['completed', 'failed'] and status2['status'] in ['completed', 'failed']:
            break
            
        time.sleep(30)  # Wait 30 seconds before next check (STAR can take a while)
    
    # Get final results
    if status1['status'] == 'completed':
        print(f"Job 1 BAM: {status1['bam_path']}")
    if status2['status'] == 'completed':
        print(f"Job 2 BAM: {status2['bam_path']}")
    
    # Clean up
    cleanup_star_jobs()

if __name__ == "__main__":
    run_star_analysis()
```

## Job Status Values

- `starting`: Job is being initialized
- `running`: Job is currently executing
- `completed`: Job finished successfully
- `failed`: Job failed with an error
- `stopped`: Job was manually stopped
- `not_found`: Job ID doesn't exist

## Important Notes

1. **Memory Management**: Jobs are stored in memory. Use `cleanup_star_jobs()` to remove completed jobs to prevent memory accumulation.

2. **Process Management**: Background jobs run in separate threads. The main process can continue while jobs are running.

3. **Error Handling**: Always check the `status` and `error` fields when monitoring jobs.

4. **Resource Usage**: STAR alignment is computationally intensive. Monitor system resources when running multiple jobs.

5. **Genome Index**: Ensure the STAR genome index is properly built and accessible before starting alignment jobs.

## STAR-Specific Considerations

### Genome Index Requirements

Before running STAR alignment, you need a properly built genome index:

```bash
# Example of building a STAR genome index
STAR --runMode genomeGenerate \
     --genomeDir /path/to/genome/index \
     --genomeFastaFiles /path/to/genome.fa \
     --runThreadN 8
```

### Output Files

STAR produces several output files:
- `*Aligned.sortedByCoord.out.bam`: Sorted BAM file with aligned reads
- `*Log.final.out`: Final alignment statistics
- `*Log.out`: Detailed alignment log
- `*SJ.out.tab`: Splice junction information

### Performance Optimization

- Use appropriate thread count based on your system
- Ensure sufficient disk space for output files
- Monitor memory usage during alignment

## Integration with Other Tools

STAR alignment can be integrated into bioinformatics pipelines:

```python
from bioopenmcp.modules.fastqc.fastqc import fastqc_background, get_fastqc_status
from bioopenmcp.modules.star_alignment.star_alignment import star_alignment_background, get_star_status

def run_rnaseq_pipeline():
    # Step 1: Quality control
    qc_job = fastqc_background("sample.fastq", job_id="qc_step")
    
    # Step 2: STAR alignment
    alignment_job = star_alignment_background(
        fastq_path="sample.fastq",
        genome_dir="/path/to/genome/index",
        output_dir="/path/to/alignment",
        job_id="alignment_step"
    )
    
    # Monitor both jobs
    while True:
        qc_status = get_fastqc_status("qc_step")
        alignment_status = get_star_status("alignment_step")
        
        if (qc_status['status'] in ['completed', 'failed'] and 
            alignment_status['status'] in ['completed', 'failed']):
            break
        
        time.sleep(30)
    
    # Process results
    if alignment_status['status'] == 'completed':
        print(f"Alignment complete: {alignment_status['bam_path']}")

if __name__ == "__main__":
    run_rnaseq_pipeline()
```

## Troubleshooting

### Common Issues

1. **STAR not found**: Use `install_star()` to install STAR or ensure it's in your PATH
2. **Genome index not found**: Verify the genome index path and ensure it's properly built
3. **Insufficient memory**: Reduce thread count or ensure sufficient system memory
4. **Disk space issues**: Ensure sufficient disk space for output files

### Debugging

Enable verbose logging to debug STAR alignment issues:

```python
# Check STAR installation
is_star_installed()

# Check job details
status = get_star_status("job_id")
print(f"Command: {status['command']}")
print(f"STDOUT: {status['stdout']}")
print(f"STDERR: {status['stderr']}")
```

## Summary

The STAR alignment background execution functionality provides:

- **Non-blocking execution** of RNA-seq alignment
- **Real-time status monitoring** of alignment progress
- **Comprehensive job management** with start, stop, and cleanup capabilities
- **Integration with MCP** for remote job management
- **Resource optimization** with configurable thread count
- **Error handling** and debugging information

This enables efficient, scalable RNA-seq analysis workflows that can handle multiple concurrent alignments while maintaining system responsiveness. 