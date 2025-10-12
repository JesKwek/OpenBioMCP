# BioOpenMCP

BioOpenMCP is a Python package for running Model Context Protocol (MCP) tools, including FastQC integration and other bioinformatics utilities with comprehensive background execution and status checking capabilities.

## Features

- **Modular design** - Organized by feature/domain for scalability
- **Background execution** - Run long-running bioinformatics tools without blocking
- **Real-time status monitoring** - Check job progress and retrieve results
- **Job management** - Start, stop, and clean up background jobs
- **CLI entry point** - Command-line interface for easy access
- **MCP integration** - Expose tools through Model Context Protocol
- **Ready for PyPI distribution**

## Supported Tools

### FastQC
- Quality control analysis for FASTQ files
- Background execution with status monitoring
- HTML report generation

### Cutadapt
- Adapter trimming for sequencing data
- Background execution with real-time monitoring
- Flexible command-line argument support

### Trim Galore
- Automated adapter and quality trimming
- Background execution with comprehensive monitoring
- Integration with FastQC and Cutadapt
- Quality and length filtering options

### STAR Alignment
- RNA-seq alignment tool
- Genome index support
- Background execution with status monitoring
- Configurable thread count for performance optimization

## Background Execution

All supported tools can be run in the background, allowing you to:

```python
from bioopenmcp.modules.fastqc.fastqc import fastqc_background, get_fastqc_status
from bioopenmcp.modules.cutadapt.cutadapt import cutadapt_background
from bioopenmcp.modules.trim_galore.trim_galore import trim_galore_background
from bioopenmcp.modules.star_alignment.star_alignment import star_alignment_background

# Start FastQC in background
job = fastqc_background("sample.fastq", job_id="qc_001")

# Check status
status = get_fastqc_status("qc_001")
print(f"Status: {status['status']}")

# Start Cutadapt in background
trim_job = cutadapt_background(
    args=["-a", "AGATCGGAAGAGC"],
    input_file="sample.fastq",
    output_file="trimmed.fastq"
)

# Start Trim Galore in background
trim_galore_job = trim_galore_background(
    fastq_path="sample.fastq",
    extra_args="--quality 20 --length 50"
)

# Start STAR alignment in background
star_job = star_alignment_background(
    fastq_path="sample.fastq",
    genome_dir="/path/to/genome/index",
    output_dir="/path/to/alignment",
    threads=8
)
```

## Documentation

- [Background Running and Status Checking](docs/background_running_status_checking.md) - Comprehensive guide to background execution
- [FastQC Background Usage](docs/fastqc_background_usage.md) - FastQC-specific background functionality
- [Feature Domain Structure](docs/feature_domain_structure.md) - Project organization and architecture

## Installation

```bash
pip install bioopenmcp
```

## Usage

```python
from bioopenmcp.modules.fastqc import fastqc_background, get_fastqc_status
from bioopenmcp.modules.searching_file.cutadapt import cutadapt_background
from bioopenmcp.modules.searching_file.trim_galore import trim_galore_background

# Run quality control
qc_job = fastqc_background("sample.fastq")

# Run adapter trimming
trim_job = cutadapt_background(
    args=["-a", "AGATCGGAAGAGC"],
    input_file="sample.fastq",
    output_file="trimmed.fastq"
)

# Run quality trimming
trim_galore_job = trim_galore_background(
    fastq_path="sample.fastq",
    extra_args="--quality 20 --length 50"
)

# Monitor jobs
status = get_fastqc_status(qc_job['job_id'])
```
