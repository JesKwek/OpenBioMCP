#!/usr/bin/env python3
"""
Script to verify MultiQC installation and fix PATH issues.
"""

import os
import subprocess
import shutil
import sys
from pathlib import Path

def check_multiqc_installation():
    """Check if MultiQC is installed and accessible."""
    print("=== MultiQC Installation Verification ===\n")
    
    # Check if multiqc is in PATH
    multiqc_path = shutil.which("multiqc")
    if multiqc_path:
        print(f"✅ MultiQC found in PATH: {multiqc_path}")
        try:
            result = subprocess.run([multiqc_path, "--version"], 
                                  capture_output=True, text=True)
            print(f"   Version: {result.stdout.strip()}")
            return True, multiqc_path
        except Exception as e:
            print(f"   ⚠️  Error getting version: {e}")
            return True, multiqc_path
    
    # Check pipx installation location
    pipx_bin_path = os.path.expanduser("~/.local/bin/multiqc")
    if os.path.exists(pipx_bin_path):
        print(f"✅ MultiQC found in pipx location: {pipx_bin_path}")
        print("⚠️  But it's not in your PATH")
        try:
            result = subprocess.run([pipx_bin_path, "--version"], 
                                  capture_output=True, text=True)
            print(f"   Version: {result.stdout.strip()}")
            return True, pipx_bin_path
        except Exception as e:
            print(f"   ⚠️  Error getting version: {e}")
            return True, pipx_bin_path
    
    print("❌ MultiQC not found")
    return False, None

def fix_path_issue():
    """Fix PATH issue by running pipx ensurepath."""
    print("\n=== Fixing PATH Issue ===")
    
    pipx_path = shutil.which("pipx")
    if not pipx_path:
        print("❌ pipx not found in PATH")
        return False
    
    try:
        print("Running 'pipx ensurepath'...")
        result = subprocess.run([pipx_path, "ensurepath"], 
                              capture_output=True, text=True)
        
        print("Output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ PATH fix attempted successfully")
            print("💡 You may need to:")
            print("   1. Restart your shell/terminal")
            print("   2. Or run: source ~/.bashrc (or ~/.zshrc)")
            return True
        else:
            print("❌ PATH fix failed")
            return False
            
    except Exception as e:
        print(f"❌ Error running pipx ensurepath: {e}")
        return False

def manual_path_instructions():
    """Provide manual PATH fix instructions."""
    print("\n=== Manual PATH Fix ===")
    
    shell = os.environ.get('SHELL', '/bin/bash')
    if 'zsh' in shell:
        config_file = "~/.zshrc"
    else:
        config_file = "~/.bashrc"
    
    print(f"Add this line to your {config_file}:")
    print('export PATH="$HOME/.local/bin:$PATH"')
    print(f"\nThen run: source {config_file}")
    print("Or restart your terminal")

def test_multiqc_functionality():
    """Test if MultiQC actually works."""
    print("\n=== Testing MultiQC Functionality ===")
    
    installed, multiqc_path = check_multiqc_installation()
    if not installed:
        print("❌ MultiQC not installed")
        return False
    
    try:
        # Test help command
        result = subprocess.run([multiqc_path, "--help"], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "usage:" in result.stdout.lower():
            print("✅ MultiQC help command works")
            return True
        else:
            print("❌ MultiQC help command failed")
            print(f"Return code: {result.returncode}")
            print(f"Output: {result.stdout[:200]}...")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ MultiQC command timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing MultiQC: {e}")
        return False

def main():
    print("MultiQC Installation Verification Script")
    print("=" * 50)
    
    # Check installation
    installed, multiqc_path = check_multiqc_installation()
    
    if not installed:
        print("\n💡 MultiQC is not installed. Run the installation function first.")
        return
    
    # If installed but not in PATH, try to fix it
    if multiqc_path and not shutil.which("multiqc"):
        print("\n🔧 Attempting to fix PATH...")
        if fix_path_issue():
            print("\n🔄 Checking again after PATH fix...")
            installed, multiqc_path = check_multiqc_installation()
        else:
            manual_path_instructions()
    
    # Test functionality
    if installed:
        if test_multiqc_functionality():
            print("\n🎉 MultiQC is installed and working correctly!")
        else:
            print("\n⚠️  MultiQC is installed but may have issues")
    
    print(f"\n📍 Final status:")
    print(f"   Installed: {installed}")
    print(f"   Path: {multiqc_path}")
    print(f"   In PATH: {shutil.which('multiqc') is not None}")

if __name__ == "__main__":
    main()
