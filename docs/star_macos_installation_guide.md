# STAR Installation Guide for macOS

This guide provides updated installation instructions for STAR (Spliced Transcripts Alignment to a Reference) on macOS, incorporating the latest compilation methods and best practices.

## Overview

STAR is a fast RNA-seq read aligner that requires proper compilation for macOS systems. This guide covers multiple installation methods, from automated package management to manual compilation.

## Prerequisites

- **macOS** (Intel or Apple Silicon)
- **Homebrew** package manager ([install here](https://brew.sh/))
- **Command Line Tools** or **Xcode** installed
- At least **2GB free disk space** for compilation

## Installation Methods

### Method 1: Homebrew Installation (Recommended)

This is the easiest and most reliable method:

```bash
# 1. Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Add bioinformatics tap
brew tap brewsci/bio

# 3. Install STAR
brew install brewsci/bio/star

# 4. Verify installation
STAR --version
```

### Method 2: Manual Compilation (Updated Steps)

Follow these steps for manual compilation with proper macOS configuration:

```bash
# 1. Install dependencies
brew install gcc wget

# 2. Download STAR source (version 2.7.11b)
wget https://github.com/alexdobin/STAR/archive/2.7.11b.tar.gz

# 3. Extract source
tar -xzf 2.7.11b.tar.gz
cd STAR-2.7.11b

# 4. Navigate to source directory
cd source

# 5. Find your GCC version
ls /usr/local/bin/g++-* || ls /opt/homebrew/bin/g++-*

# 6. Compile STAR for macOS (adjust GCC version as needed)
# For Intel Macs:
make STARforMacStatic CXX=/usr/local/bin/g++-13

# For Apple Silicon Macs:
make STARforMacStatic CXX=/opt/homebrew/bin/g++-13

# 7. Install STAR binary
sudo cp STAR /usr/local/bin/

# 8. Make executable
sudo chmod +x /usr/local/bin/STAR

# 9. Verify installation
STAR --version
```

### Method 3: Git Clone Alternative

```bash
# 1. Install dependencies
brew install gcc git

# 2. Clone STAR repository
git clone https://github.com/alexdobin/STAR.git

# 3. Navigate to source directory
cd STAR/source

# 4. Compile and install (adjust GCC version as needed)
make STARforMacStatic CXX=/usr/local/bin/g++-13 && sudo cp STAR /usr/local/bin/
```

### Method 4: Automated Installation via OpenBioMCP

Use the built-in installation function:

```python
from bioopenmcp.modules.star_alignment.star_alignment import install_star

# This will automatically:
# 1. Try Homebrew installation
# 2. Fall back to conda if available  
# 3. Compile from source with multiple strategies
result = install_star()
print(result)
```

## Troubleshooting

### Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| **GCC not found** | Run `brew install gcc` and check versions with `ls /usr/local/bin/g++-*` |
| **Permission denied** | Use `sudo` prefix: `sudo cp STAR /usr/local/bin/` |
| **STAR command not found** | Check PATH: `echo $PATH` (ensure `/usr/local/bin` is included) |
| **Compilation fails** | Try different GCC versions or install libomp: `brew install libomp` |
| **Apple Silicon issues** | Use `/opt/homebrew` paths instead of `/usr/local` |

### System-Specific Notes

#### Intel Macs
- GCC path: `/usr/local/bin/g++-*`
- Install path: `/usr/local/bin/STAR`
- Standard Homebrew compilation should work

#### Apple Silicon Macs
- GCC path: `/opt/homebrew/bin/g++-*`
- Install path: `/usr/local/bin/STAR`
- May need ARM64-compatible GCC and different paths

## Verification

After installation, verify STAR is working:

```bash
# Check version
STAR --version

# Check location
which STAR

# View help
STAR --help
```

Expected output should show STAR version information and help text.

## Key Points

1. **STARforMacStatic target**: Specifically designed for macOS, creates a static binary
2. **GCC versions**: May vary (8, 9, 10, 11, 12, 13) - use the highest available version
3. **Path differences**: Apple Silicon Macs use `/opt/homebrew`, Intel Macs use `/usr/local`
4. **Multiple strategies**: The automated installer tries various compilation approaches
5. **OpenMP support**: Install `libomp` for parallel processing capabilities

## Integration with OpenBioMCP

Once STAR is installed, you can use it through the OpenBioMCP tools:

```python
from bioopenmcp.modules.star_alignment import (
    run_star_alignment,
    star_alignment_background,
    generate_star_genome_index,
    is_star_installed,
    get_macos_manual_installation_guide
)

# Check if STAR is installed
status = is_star_installed()
print(status)

# Get detailed installation guide
guide = get_macos_manual_installation_guide()
print(guide)

# Run alignment (example)
bam_file = run_star_alignment(
    fastq_path="sample.fastq",
    genome_dir="/path/to/star_genome_index",
    output_dir="/path/to/output"
)
```

## Additional Resources

- [STAR GitHub Repository](https://github.com/alexdobin/STAR)
- [STAR Manual](https://github.com/alexdobin/STAR/blob/master/doc/STARmanual.pdf)
- [Homebrew](https://brew.sh/)
- [Bioconda STAR Package](https://bioconda.github.io/recipes/star/README.html)

## Support

If you encounter issues with STAR installation or usage within OpenBioMCP, please check:

1. System requirements using `check_system_requirements()`
2. Installation status using `is_star_installed()`
3. Detailed installation guide using `get_macos_manual_installation_guide()`

The automated installer will attempt multiple compilation strategies and provide detailed output for troubleshooting.
