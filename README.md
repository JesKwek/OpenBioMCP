# OpenBioMCP

OpenBioMCP is a Python package for running Model Context Protocol (MCP) tools, including FastQC integration and other bioinformatics utilities with comprehensive background execution and status checking capabilities.

## Installation

```bash
pip install openbiomcp
```

## MCP Configuration

After installation, you need to configure the MCP server in Claude Desktop:

### Step 1: Find the installation path

**Mac:**
```bash
which openbiomcp
```
Example output: `/opt/anaconda3/bin/openbiomcp`

**Windows:**
```cmd
where openbiomcp
```
Copy the path from the output.

### Step 2: Configure Claude Desktop

Add the following configuration to your Claude Desktop settings:

```json
{
  "mcpServers": {
    "BioOpenMCP": {
      "command": "<PATH>"
    }
  }
}
```

**Example for Mac:**
```json
{
  "mcpServers": {
    "BioOpenMCP": {
      "command": "/opt/anaconda3/bin/openbiomcp"
    }
  }
}
```

Replace `<PATH>` with the actual path from Step 1.

### Step 3: Restart Claude Desktop

After adding the configuration, restart Claude Desktop to load the MCP server.


## Features

- **Modular design** - Organized by feature/domain for scalability
- **Background execution** - Run long-running bioinformatics tools without blocking
- **Real-time status monitoring** - Check job progress and retrieve results
- **Job management** - Start, stop, and clean up background jobs
- **CLI entry point** - Command-line interface for easy access
- **MCP integration** - Expose tools through Model Context Protocol
- **Ready for PyPI distribution**

## Available Bioinformatics Tools

| Tool | Purpose | Trigger Prompt Examples |
|------|---------|------------------------|
| **FastQC** | Quality control analysis for FASTQ files | "Run FastQC on my sample.fastq file"<br>"Check the quality of my sequencing data"<br>"Generate a quality report for sample_R1.fastq" |
| **Cutadapt** | Adapter trimming for sequencing data | "Trim adapters from my FASTQ file"<br>"Remove adapter sequences using cutadapt"<br>"Clean my sequencing data with adapter trimming" |
| **Trim Galore** | Automated adapter and quality trimming | "Run Trim Galore on my FASTQ file"<br>"Quality trim my sequencing data"<br>"Automatically trim adapters and low quality bases" |
| **STAR Alignment** | RNA-seq alignment tool | "Align my FASTQ files to the genome using STAR"<br>"Run RNA-seq alignment with STAR"<br>"Map my reads to the reference genome" |
| **MultiQC** | Aggregate bioinformatics analysis results | "Generate a MultiQC report for my analysis"<br>"Summarize all my QC results"<br>"Create a comprehensive report of my bioinformatics analysis" |

### Tool Categories

#### Quality Control
- **FastQC**: Comprehensive quality control analysis
- **MultiQC**: Aggregate and visualize QC results

#### Data Processing
- **Cutadapt**: Precise adapter trimming
- **Trim Galore**: Automated quality and adapter trimming

#### Alignment
- **STAR**: High-performance RNA-seq alignment
- **Genome Indexing**: Build STAR genome indices

#### Background Execution
All tools support background execution with real-time monitoring:
- Start jobs in the background
- Check job status and progress
- Retrieve results when complete
- Stop or cancel running jobs
- Clean up completed jobs

## Usage Examples

### FastQC Examples

#### Install FastQC
```
Install FastQC on my system
```
or
```
Check if FastQC is installed and install it if needed
```

#### Run FastQC in Background
```
Run FastQC on my sample.fastq file in the background
```
or
```
Check the quality of my sequencing data with FastQC
```

#### Check FastQC Status
```
Check the status of my FastQC job
```
or
```
What's the progress of my quality control analysis?
```

#### Get FastQC Results
```
Get the FastQC report for my analysis
```
or
```
Show me the quality control results
```

### Cutadapt Examples

#### Install Cutadapt
```
Install cutadapt for adapter trimming
```

#### Run Cutadapt in Background
```
Trim adapters from my FASTQ file using cutadapt
```
or
```
Remove adapter sequences from sample.fastq
```

#### Check Cutadapt Status
```
Check the status of my adapter trimming job
```

### Trim Galore Examples

#### Install Trim Galore
```
Install Trim Galore for automated trimming
```

#### Run Trim Galore in Background
```
Run Trim Galore on my FASTQ file
```
or
```
Quality trim my sequencing data with Trim Galore
```

#### Check Trim Galore Status
```
Check the status of my Trim Galore job
```

### STAR Alignment Examples

#### Install STAR
```
Install STAR for RNA-seq alignment
```

#### Generate Genome Index
```
Generate a STAR genome index for my reference genome
```
or
```
Build a genome index for STAR alignment
```

#### Run STAR Alignment in Background
```
Align my FASTQ files to the genome using STAR
```
or
```
Run RNA-seq alignment with STAR on my data
```

#### Check STAR Status
```
Check the status of my STAR alignment job
```

### MultiQC Examples

#### Install MultiQC
```
Install MultiQC for report aggregation
```

#### Run MultiQC
```
Generate a MultiQC report for my analysis
```
or
```
Summarize all my QC results with MultiQC
```

### Job Management Examples

#### List All Jobs
```
Show me all running background jobs
```
or
```
List my current bioinformatics jobs
```

#### Stop a Job
```
Stop my FastQC job
```
or
```
Cancel my running alignment
```

#### Clean Up Jobs
```
Clean up completed jobs
```
or
```
Remove finished job information
```

## Advanced Usage

### Custom Parameters
```
Run FastQC on sample.fastq with custom parameters
```

```
Trim adapters with specific adapter sequence: AGATCGGAAGAGC
```

```
Run Trim Galore with quality threshold 20 and minimum length 50
```

### Paired-End Analysis
```
Run FastQC on paired-end reads: sample_R1.fastq and sample_R2.fastq
```

```
Align paired-end RNA-seq data with STAR
```

### Batch Processing
```
Run FastQC on all FASTQ files in my directory
```

```
Generate MultiQC report for all my analysis results
```

