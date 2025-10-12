#!/usr/bin/env python3
"""
Test script to verify the corrected MultiQC installation suggestions.

This script demonstrates the correct way to install MultiQC on systems
with externally-managed Python environments.
"""

import subprocess
import shutil
import sys
from pathlib import Path

# Add the src directory to the Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def check_command_availability():
    """Check which installation tools are available."""
    tools = {
        'python3': shutil.which('python3'),
        'pip': shutil.which('pip') or shutil.which('pip3'),
        'pipx': shutil.which('pipx'),
        'brew': shutil.which('brew'),
        'multiqc': shutil.which('multiqc')
    }
    
    print("=== System Tool Availability ===")
    for tool, path in tools.items():
        status = "✓ Available" if path else "✗ Not found"
        print(f"{tool:10}: {status}" + (f" ({path})" if path else ""))
    
    return tools

def test_installation_suggestions():
    """Test the installation suggestions from our function."""
    print("\n=== Testing Installation Function ===")
    
    try:
        from bioopenmcp.modules.multiqc.multiqc import install_multiqc
        
        result = install_multiqc()
        
        print(f"MultiQC installed: {result['multiqc_installed']}")
        print(f"Installation method: {result.get('installation_method', 'None')}")
        
        if not result['multiqc_installed']:
            print(f"Error: {result['error']}")
            print("\nSuggestions:")
            for i, suggestion in enumerate(result['suggestions'], 1):
                print(f"  {i}. {suggestion}")
        
        return result
        
    except ImportError as e:
        print(f"Failed to import MultiQC module: {e}")
        return None

def demonstrate_correct_installation():
    """Show the correct installation commands."""
    print("\n=== Correct Installation Commands ===")
    
    tools = check_command_availability()
    
    if tools['multiqc']:
        print("✓ MultiQC is already installed!")
        try:
            result = subprocess.run(['multiqc', '--version'], 
                                  capture_output=True, text=True)
            print(f"  Version: {result.stdout.strip()}")
        except:
            print("  (Could not get version)")
        return
    
    print("\nRecommended installation methods:")
    
    if tools['pipx']:
        print("\n1. Using pipx (RECOMMENDED - already available):")
        print("   pipx install multiqc")
    elif tools['brew']:
        print("\n1. Using brew + pipx (RECOMMENDED for your system):")
        print("   brew install pipx")
        print("   pipx install multiqc")
    else:
        print("\n1. Install pipx first:")
        print("   python3 -m pip install --user pipx")
        print("   pipx install multiqc")
    
    print("\n2. Using virtual environment (ALTERNATIVE):")
    print("   python3 -m venv multiqc_env")
    print("   source multiqc_env/bin/activate")
    print("   pip install multiqc")
    
    print("\n3. Using --break-system-packages (NOT RECOMMENDED):")
    print("   pip install multiqc --break-system-packages")

def main():
    print("MultiQC Installation Test Script")
    print("=" * 40)
    
    tools = check_command_availability()
    result = test_installation_suggestions()
    demonstrate_correct_installation()
    
    print("\n=== Summary ===")
    if tools['multiqc']:
        print("✓ MultiQC is ready to use!")
    else:
        print("✗ MultiQC needs to be installed")
        print("  Recommendation: Use pipx for the cleanest installation")
        
        if tools['brew'] and not tools['pipx']:
            print("  Next step: brew install pipx && pipx install multiqc")
        elif tools['pipx']:
            print("  Next step: pipx install multiqc")
        else:
            print("  Next step: Create a virtual environment and use pip")

if __name__ == "__main__":
    main()
