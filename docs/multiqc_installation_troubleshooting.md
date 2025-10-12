# MultiQC Installation Troubleshooting Guide

This guide addresses common installation issues for MultiQC, particularly on macOS systems with externally-managed Python environments.

## Common Error: "No available formula with the name 'multiqc'"

**Problem:** When running `brew install multiqc`, you get:
```
Warning: No available formula with the name "multiqc". Did you mean multitime?
```

**Root Cause:** MultiQC is **NOT available in Homebrew** at all (including brewsci/bio tap). It's only available via PyPI.

### Correct Solution:
```bash
# Install pipx via Homebrew first
brew install pipx

# Then install MultiQC via pipx
pipx install multiqc
```

## Common Error: "externally-managed-environment"

**Problem:** When using pip, you get:
```
error: externally-managed-environment

× This environment is externally managed
╰─> To install Python packages system-wide, try brew install
    xyz, where xyz is the package you are trying to
    install.
```

**Solution:** The `install_multiqc()` function now automatically handles this by trying multiple installation methods:

### Automatic Installation Order:
1. **pipx** (if available) - Creates isolated environment
2. **pipx via brew** - Install pipx using Homebrew, then install MultiQC
3. **pip --user** - Installs to user directory
4. **pip** (fallback) - System-wide installation

## Installation Methods Comparison

| Method | Pros | Cons | When to Use |
|--------|------|------|-------------|
| **pipx** | ✅ Isolated environment<br>✅ No conflicts<br>✅ Easy to manage | ❌ Requires pipx installation | **Recommended** - Best for applications |
| **pipx via brew** | ✅ System package manager for pipx<br>✅ Isolated environment<br>✅ No Python env issues | ❌ macOS only<br>❌ Two-step process | **Good** - macOS users |
| **pip --user** | ✅ No system conflicts<br>✅ Works on most systems | ❌ PATH issues possible<br>❌ User directory clutter | **Fallback** - When others fail |
| **Virtual Environment** | ✅ Full isolation<br>✅ Reproducible | ❌ Manual management<br>❌ Activation required | **Manual** - Development work |

## Step-by-Step Solutions

### Option 1: Using pipx (Recommended)
```bash
# Install pipx if not available
brew install pipx

# Install MultiQC via pipx
pipx install multiqc

# Verify installation
multiqc --version
```

### Option 2: Using Homebrew + pipx
```bash
# Install pipx via Homebrew
brew install pipx

# Install MultiQC via pipx
pipx install multiqc

# Verify installation
multiqc --version
```

### Option 3: Using Virtual Environment
```bash
# Create virtual environment
python3 -m venv multiqc_env

# Activate environment
source multiqc_env/bin/activate

# Install MultiQC
pip install multiqc

# Verify installation
multiqc --version

# Deactivate when done
deactivate
```

### Option 4: User Installation (Not Recommended)
```bash
# Install to user directory
pip install --user multiqc

# May need to add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Verify installation
multiqc --version
```

## Using the Automated Installation Function

The `install_multiqc()` function automatically tries all these methods:

```python
from bioopenmcp.modules.multiqc.multiqc import install_multiqc

# Attempt installation
result = install_multiqc()

if result["multiqc_installed"]:
    print(f"✅ Success! Installed via: {result['installation_method']}")
else:
    print("❌ Installation failed")
    print("Suggestions:")
    for suggestion in result["suggestions"]:
        print(f"  • {suggestion}")
```

## Expected Results Based on Your System

### System with Homebrew + No pipx:
```python
{
  "multiqc_installed": True,
  "installation_method": "brew (brewsci/bio)",
  "pipx_available": False,
  "brew_available": True,
  "suggestions": []
}
```

### System with pipx:
```python
{
  "multiqc_installed": True,
  "installation_method": "pipx",
  "pipx_available": True,
  "brew_available": True,
  "suggestions": []
}
```

### System where all methods fail:
```python
{
  "multiqc_installed": False,
  "installation_method": None,
  "error": "All installation methods failed...",
  "suggestions": [
    "Install pipx: brew install pipx (then run: pipx install multiqc)",
    "Try bioinformatics tap: brew tap brewsci/bio && brew install brewsci/bio/multiqc",
    "Create virtual environment: python3 -m venv venv && source venv/bin/activate && pip install multiqc"
  ]
}
```

## Verification Commands

After installation, verify MultiQC works:

```bash
# Check version
multiqc --version

# Check help
multiqc --help

# Test with sample data (if available)
multiqc /path/to/analysis/results --dry-run
```

## Common Issue: pipx PATH Problem

**Problem:** MultiQC installs successfully via pipx but shows as "not installed":
```
⚠️  Note: '/Users/username/.local/bin' is not on your PATH environment
    variable. These apps will not be globally accessible until your PATH is
    updated. Run `pipx ensurepath` to automatically add it...
```

**Root Cause:** pipx installs applications to `~/.local/bin` but this directory is not in your shell's PATH.

**Automatic Fix:** The updated installation function now automatically runs `pipx ensurepath` after successful installation.

**Manual Fix if needed:**
```bash
# Fix PATH automatically
pipx ensurepath

# Then restart your shell or run:
source ~/.bashrc  # for bash
source ~/.zshrc   # for zsh

# Or manually add to your shell config:
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
```

## Common PATH Issues

If MultiQC is installed but not found:

### For pipx installations:
```bash
# Check pipx bin directory
pipx list

# Add to PATH if needed
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### For user installations:
```bash
# Check user bin directory
ls ~/.local/bin/

# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### For Homebrew installations:
```bash
# Usually works automatically, but check
brew --prefix

# If issues, ensure Homebrew is in PATH
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc  # Apple Silicon
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc     # Intel Mac
source ~/.zshrc
```

## Summary

The updated MultiQC installation function now:

1. ✅ **Handles brewsci/bio tap** - Automatically adds and uses the bioinformatics tap
2. ✅ **Tries pipx first** - Uses the recommended isolation method
3. ✅ **Falls back gracefully** - Multiple fallback options
4. ✅ **Provides clear guidance** - Specific suggestions based on your system
5. ✅ **Detects system capabilities** - Knows what tools are available

This should resolve the "No available formula" and "externally-managed-environment" errors you encountered!
