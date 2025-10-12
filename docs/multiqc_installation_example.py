#!/usr/bin/env python3
"""
Example script demonstrating robust MultiQC installation handling.

This script shows how to handle the common externally-managed-environment
error (PEP 668) that occurs on modern Python installations.
"""

import sys
import json
from pathlib import Path

# Add the src directory to the Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bioopenmcp.modules.multiqc.multiqc import install_multiqc, is_multiqc_installed

def main():
    print("=== MultiQC Installation Example ===\n")
    
    # First, check if MultiQC is already installed
    print("1. Checking current MultiQC installation status...")
    status = is_multiqc_installed()
    
    if status["multiqc_installed"]:
        print(f"✓ MultiQC is already installed at: {status['multiqc_path']}")
        print(f"  Version: {status['multiqc_version']}")
        return
    else:
        print("✗ MultiQC is not currently installed")
    
    print(f"  Python available: {status['python_available']}")
    print(f"  pip available: {status['pip_available']}")
    
    # Attempt installation
    print("\n2. Attempting to install MultiQC...")
    print("   Trying multiple methods to handle system restrictions...")
    
    result = install_multiqc()
    
    if result["multiqc_installed"]:
        print(f"✓ MultiQC installed successfully!")
        print(f"  Installation method: {result['installation_method']}")
        print(f"  Available tools: pipx={result['pipx_available']}, brew={result['brew_available']}")
        
        if result["multiqc_install_output"]:
            print(f"  Installation output: {result['multiqc_install_output'][:200]}...")
    
    else:
        print("✗ MultiQC installation failed")
        print(f"  Error: {result['error']}")
        print(f"  Available tools: pipx={result['pipx_available']}, brew={result['brew_available']}")
        
        if result["suggestions"]:
            print("\n  💡 Suggestions for manual installation:")
            for i, suggestion in enumerate(result["suggestions"], 1):
                print(f"     {i}. {suggestion}")
        
        if result["multiqc_install_output"]:
            print(f"\n  📋 Installation attempts log:")
            print("    " + result["multiqc_install_output"].replace("\n", "\n    "))
    
    # Show the full result for debugging
    print(f"\n3. Full installation result (JSON):")
    print(json.dumps(result, indent=2))

def demonstrate_externally_managed_error():
    """
    Example of how the function handles externally-managed-environment errors.
    """
    print("\n=== Handling Externally-Managed Environment ===")
    print("When you encounter this error:")
    print("""
error: externally-managed-environment

× This environment is externally managed
╰─> To install Python packages system-wide, try brew install
    xyz, where xyz is the package you are trying to
    install.
    """)
    
    print("The install_multiqc() function automatically tries these alternatives:")
    print("1. pipx install multiqc (recommended)")
    print("2. brew install multiqc (on macOS)")
    print("3. pip install --user multiqc")
    print("4. pip install multiqc (last resort)")
    
    print("\nAnd provides helpful suggestions if all methods fail.")

if __name__ == "__main__":
    main()
    demonstrate_externally_managed_error()
