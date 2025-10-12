import os
import glob
import shutil
import subprocess
import platform
import threading
import time
import json
import datetime
from typing import Dict, Optional, List

# Global dictionaries to track background MultiQC processes
_multiqc_processes: Dict[str, Dict] = {}  # For serializable job info
_multiqc_process_objects: Dict[str, subprocess.Popen] = {}  # For process objects only

def multiqc(input_dir: str, output_dir: str = None, config_file: str = None, extra_args: str = "") -> str:
    """Runs MultiQC on a directory containing bioinformatics analysis results.
    Args:
        input_dir: Directory containing analysis results to aggregate
        output_dir: Output directory for MultiQC report (defaults to input_dir/multiqc_report)
        config_file: Optional MultiQC configuration file
        extra_args: Additional command-line arguments for MultiQC
    Returns:
        Path to the MultiQC HTML report
    """
    # Check if input directory exists
    if not os.path.exists(input_dir):
        raise RuntimeError(f"Input directory not found: {input_dir}")
    
    # Set default output directory if not provided
    if output_dir is None:
        output_dir = os.path.join(input_dir, "multiqc_report")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Try to find MultiQC in system
    multiqc_path = shutil.which("multiqc")
    if not multiqc_path:
        # Fallback paths
        conda_multiqc = "/opt/anaconda3/bin/multiqc"
        if os.path.exists(conda_multiqc):
            multiqc_path = conda_multiqc
        else:
            raise RuntimeError("MultiQC not found. Please install MultiQC using: pip install multiqc")
    
    # Check if the MultiQC executable exists
    if not os.path.exists(multiqc_path):
        raise RuntimeError(f"MultiQC not found at {multiqc_path}. Please check your installation.")
    
    # Build command
    cmd = [multiqc_path, input_dir, "--outdir", output_dir]
    
    # Add config file if provided
    if config_file and os.path.exists(config_file):
        cmd.extend(["--config", config_file])
    
    # Add extra arguments if provided
    if extra_args:
        cmd.extend(extra_args.split())
    
    # Run MultiQC and capture output
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Check if the output file was created
    report_path = os.path.join(output_dir, "multiqc_report.html")
    if not os.path.exists(report_path):
        error_msg = result.stderr if result.stderr else "Unknown error"
        raise RuntimeError(f"MultiQC failed to create report: {error_msg}")
    
    return report_path

def multiqc_background(input_dir: str, output_dir: str = None, config_file: str = None, 
                      extra_args: str = "", job_id: Optional[str] = None) -> Dict:
    """Runs MultiQC in the background and returns job information.
    Args:
        input_dir: Directory containing analysis results to aggregate
        output_dir: Output directory for MultiQC report (defaults to input_dir/multiqc_report)
        config_file: Optional MultiQC configuration file
        extra_args: Additional command-line arguments for MultiQC
        job_id: Optional custom job ID. If not provided, will be auto-generated
    Returns:
        Dictionary containing job_id, status, and other job information
    """
    global _multiqc_processes
    
    # Generate job ID if not provided
    if job_id is None:
        dir_name = os.path.basename(input_dir.rstrip('/'))
        job_id = f"multiqc_{dir_name}_{int(time.time())}"
    
    # Check if job_id already exists
    if job_id in _multiqc_processes:
        raise RuntimeError(f"Job ID '{job_id}' already exists. Please use a different job ID.")
    
    # Check if input directory exists
    if not os.path.exists(input_dir):
        raise RuntimeError(f"Input directory not found: {input_dir}")
    
    # Set default output directory if not provided
    if output_dir is None:
        output_dir = os.path.join(input_dir, "multiqc_report")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Try to find MultiQC in system
    multiqc_path = shutil.which("multiqc")
    if not multiqc_path:
        # Fallback paths
        conda_multiqc = "/opt/anaconda3/bin/multiqc"
        if os.path.exists(conda_multiqc):
            multiqc_path = conda_multiqc
        else:
            raise RuntimeError("MultiQC not found. Please install MultiQC using: pip install multiqc")
    
    # Check if the MultiQC executable exists
    if not os.path.exists(multiqc_path):
        raise RuntimeError(f"MultiQC not found at {multiqc_path}. Please check your installation.")
    
    # Build command
    cmd = [multiqc_path, input_dir, "--outdir", output_dir]
    
    # Add config file if provided
    if config_file and os.path.exists(config_file):
        cmd.extend(["--config", config_file])
    
    # Add extra arguments if provided
    if extra_args:
        cmd.extend(extra_args.split())
    
    # Initialize job info
    job_info = {
        "job_id": job_id,
        "input_dir": input_dir,
        "output_dir": output_dir,
        "config_file": config_file,
        "extra_args": extra_args,
        "status": "starting",
        "start_time": time.time(),
        "end_time": None,
        "process": None,
        "stdout": "",
        "stderr": "",
        "return_code": None,
        "report_path": None,
        "error": None
    }
    
    def run_multiqc():
        """Background function to run MultiQC"""
        try:
            job_info["status"] = "running"
            # Start the process
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            job_info["process"] = process
            
            # Wait for completion
            stdout, stderr = process.communicate()
            job_info["stdout"] = stdout
            job_info["stderr"] = stderr
            job_info["return_code"] = process.returncode
            job_info["end_time"] = time.time()
            
            # Check if the output file was created
            report_path = os.path.join(output_dir, "multiqc_report.html")
            
            if process.returncode == 0 and os.path.exists(report_path):
                job_info["status"] = "completed"
                job_info["report_path"] = report_path
            else:
                job_info["status"] = "failed"
                job_info["error"] = stderr if stderr else "Unknown error"
                
        except Exception as e:
            job_info["status"] = "failed"
            job_info["error"] = str(e)
            job_info["end_time"] = time.time()
    
    # Start the background thread
    thread = threading.Thread(target=run_multiqc)
    thread.daemon = True
    thread.start()
    
    # Store job info
    _multiqc_processes[job_id] = job_info
    
    return {
        "job_id": job_id,
        "status": "started",
        "message": f"MultiQC job '{job_id}' started in background"
    }

def get_multiqc_status(job_id: str) -> Dict:
    """Get the status of a background MultiQC job.
    Args:
        job_id: The job ID to check
    Returns:
        Dictionary containing job status and information
    """
    global _multiqc_processes
    
    if job_id not in _multiqc_processes:
        return {
            "job_id": job_id,
            "status": "not_found",
            "error": f"Job ID '{job_id}' not found"
        }
    
    job_info = _multiqc_processes[job_id]
    
    # Create a serializable copy of job info (excluding the process object)
    serializable_info = {
        "job_id": job_info["job_id"],
        "input_dir": job_info["input_dir"],
        "output_dir": job_info["output_dir"],
        "config_file": job_info["config_file"],
        "extra_args": job_info["extra_args"],
        "status": job_info["status"],
        "start_time": job_info["start_time"],
        "end_time": job_info["end_time"],
        "stdout": job_info["stdout"],
        "stderr": job_info["stderr"],
        "return_code": job_info["return_code"],
        "report_path": job_info["report_path"],
        "error": job_info["error"]
    }
    
    # Convert timestamps to readable format
    if serializable_info["start_time"]:
        start_dt = datetime.datetime.fromtimestamp(serializable_info["start_time"])
        serializable_info["start_time_readable"] = start_dt.strftime("%I:%M:%S %p on %B %d, %Y")
    
    if serializable_info["end_time"]:
        end_dt = datetime.datetime.fromtimestamp(serializable_info["end_time"])
        serializable_info["end_time_readable"] = end_dt.strftime("%I:%M:%S %p on %B %d, %Y")
    
    # Calculate runtime if job is finished
    if serializable_info["end_time"] and serializable_info["start_time"]:
        runtime_seconds = serializable_info["end_time"] - serializable_info["start_time"]
        serializable_info["runtime_seconds"] = runtime_seconds
        
        # Format runtime in a readable way
        if runtime_seconds < 60:
            serializable_info["runtime_readable"] = f"{runtime_seconds:.1f} seconds"
        elif runtime_seconds < 3600:
            minutes = runtime_seconds / 60
            serializable_info["runtime_readable"] = f"{minutes:.1f} minutes"
        else:
            hours = runtime_seconds / 3600
            serializable_info["runtime_readable"] = f"{hours:.1f} hours"
    
    return serializable_info

def list_multiqc_jobs() -> Dict:
    """List all background MultiQC jobs and their statuses.
    Returns:
        Dictionary containing all job information
    """
    global _multiqc_processes
    
    jobs = {}
    for job_id, job_info in _multiqc_processes.items():
        jobs[job_id] = get_multiqc_status(job_id)
    
    return {
        "total_jobs": len(jobs),
        "jobs": jobs
    }

def stop_multiqc_job(job_id: str) -> Dict:
    """Stop a running MultiQC job.
    Args:
        job_id: The job ID to stop
    Returns:
        Dictionary containing stop operation result
    """
    global _multiqc_processes
    
    if job_id not in _multiqc_processes:
        return {
            "job_id": job_id,
            "status": "not_found",
            "error": f"Job ID '{job_id}' not found"
        }
    
    job_info = _multiqc_processes[job_id]
    
    if job_info["status"] in ["completed", "failed"]:
        return {
            "job_id": job_id,
            "status": "already_finished",
            "message": f"Job '{job_id}' has already finished with status: {job_info['status']}"
        }
    
    if job_info["process"] is not None:
        try:
            job_info["process"].terminate()
            # Wait a bit for graceful termination
            time.sleep(1)
            if job_info["process"].poll() is None:
                job_info["process"].kill()
            
            job_info["status"] = "stopped"
            job_info["end_time"] = time.time()
            
            return {
                "job_id": job_id,
                "status": "stopped",
                "message": f"Job '{job_id}' has been stopped"
            }
        except Exception as e:
            return {
                "job_id": job_id,
                "status": "error",
                "error": f"Failed to stop job: {str(e)}"
            }
    
    return {
        "job_id": job_id,
        "status": "error",
        "error": "No process found to stop"
    }

def cleanup_multiqc_jobs(completed_only: bool = True) -> Dict:
    """Clean up completed or failed MultiQC jobs from memory.
    Args:
        completed_only: If True, only remove completed/failed jobs. If False, remove all jobs.
    Returns:
        Dictionary containing cleanup results
    """
    global _multiqc_processes
    
    jobs_to_remove = []
    for job_id, job_info in _multiqc_processes.items():
        if completed_only:
            if job_info["status"] in ["completed", "failed", "stopped"]:
                jobs_to_remove.append(job_id)
        else:
            jobs_to_remove.append(job_id)
    
    for job_id in jobs_to_remove:
        del _multiqc_processes[job_id]
    
    return {
        "removed_jobs": len(jobs_to_remove),
        "remaining_jobs": len(_multiqc_processes),
        "removed_job_ids": jobs_to_remove
    }

def install_multiqc() -> dict:
    """Install MultiQC if not present. Returns a summary of actions taken and installation status."""
    result = {
        "multiqc_installed": False,
        "multiqc_install_attempted": False,
        "multiqc_install_output": None,
        "python_available": False,
        "pip_available": False,
        "pipx_available": False,
        "brew_available": False,
        "installation_method": None,
        "error": None,
        "suggestions": []
    }
    
    # Check Python
    python_path = shutil.which("python") or shutil.which("python3")
    if python_path:
        result["python_available"] = True
    else:
        result["error"] = "Python not found. Please install Python first."
        return result
    
    # Check pip
    pip_path = shutil.which("pip") or shutil.which("pip3")
    if pip_path:
        result["pip_available"] = True
    
    # Check pipx
    pipx_path = shutil.which("pipx")
    if pipx_path:
        result["pipx_available"] = True
    
    # Check brew (macOS)
    brew_path = shutil.which("brew")
    if brew_path and platform.system() == "Darwin":
        result["brew_available"] = True
    
    # Check MultiQC
    multiqc_path = shutil.which("multiqc")
    if multiqc_path:
        result["multiqc_installed"] = True
        return result
    
    # Try multiple installation methods
    result["multiqc_install_attempted"] = True
    installation_attempts = []
    
    # Method 1: Try pipx first (recommended for applications)
    if result["pipx_available"]:
        try:
            proc = subprocess.run([pipx_path, "install", "multiqc"], 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            installation_attempts.append(f"pipx install attempt: {proc.stdout + proc.stderr}")
            
            if proc.returncode == 0:
                multiqc_path = shutil.which("multiqc")
                if multiqc_path:
                    result["multiqc_installed"] = True
                    result["installation_method"] = "pipx"
                    result["multiqc_install_output"] = "\n".join(installation_attempts)
                    return result
        except Exception as e:
            installation_attempts.append(f"pipx install failed: {e}")
    
    # Method 2: Install pipx via brew if available (MultiQC is not in Homebrew)
    if result["brew_available"] and not result["pipx_available"]:
        try:
            # Install pipx first
            proc_pipx = subprocess.run([brew_path, "install", "pipx"], 
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            installation_attempts.append(f"brew install pipx attempt: {proc_pipx.stdout + proc_pipx.stderr}")
            
            if proc_pipx.returncode == 0:
                # Check if pipx is now available
                pipx_path_new = shutil.which("pipx")
                if pipx_path_new:
                    # Now try to install MultiQC with pipx
                    proc_multiqc = subprocess.run([pipx_path_new, "install", "multiqc"], 
                                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    installation_attempts.append(f"pipx install multiqc attempt: {proc_multiqc.stdout + proc_multiqc.stderr}")
                    
                    if proc_multiqc.returncode == 0:
                        # Check multiple possible locations for multiqc after pipx install
                        multiqc_path = shutil.which("multiqc")
                        if not multiqc_path:
                            # pipx installs to ~/.local/bin by default
                            import os
                            pipx_bin_path = os.path.expanduser("~/.local/bin/multiqc")
                            if os.path.exists(pipx_bin_path):
                                multiqc_path = pipx_bin_path
                        
                        if multiqc_path:
                            result["multiqc_installed"] = True
                            result["installation_method"] = "pipx (via brew)"
                            result["multiqc_install_output"] = "\n".join(installation_attempts)
                            
                            # Fix PATH automatically if needed
                            if "not on your PATH" in proc_multiqc.stdout:
                                try:
                                    # Run pipx ensurepath to fix PATH
                                    proc_path = subprocess.run([pipx_path_new, "ensurepath"], 
                                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                                    installation_attempts.append(f"pipx ensurepath: {proc_path.stdout + proc_path.stderr}")
                                    result["path_fixed"] = proc_path.returncode == 0
                                    if proc_path.returncode == 0:
                                        result["path_fix_message"] = "PATH updated. You may need to restart your shell or run 'source ~/.bashrc' (or ~/.zshrc)"
                                except Exception as e:
                                    result["path_fix_error"] = str(e)
                            
                            return result
        except Exception as e:
            installation_attempts.append(f"brew install pipx + pipx install multiqc failed: {e}")
    
    # Method 3: Try pip with --user flag
    if result["pip_available"]:
        try:
            proc = subprocess.run([pip_path, "install", "--user", "multiqc"], 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            installation_attempts.append(f"pip --user install attempt: {proc.stdout + proc.stderr}")
            
            if proc.returncode == 0:
                multiqc_path = shutil.which("multiqc")
                if multiqc_path:
                    result["multiqc_installed"] = True
                    result["installation_method"] = "pip --user"
                    result["multiqc_install_output"] = "\n".join(installation_attempts)
                    return result
        except Exception as e:
            installation_attempts.append(f"pip --user install failed: {e}")
    
    # Method 4: Try regular pip (might fail with externally-managed-environment)
    if result["pip_available"]:
        try:
            proc = subprocess.run([pip_path, "install", "multiqc"], 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            installation_attempts.append(f"pip install attempt: {proc.stdout + proc.stderr}")
            
            if proc.returncode == 0:
                multiqc_path = shutil.which("multiqc")
                if multiqc_path:
                    result["multiqc_installed"] = True
                    result["installation_method"] = "pip"
                    result["multiqc_install_output"] = "\n".join(installation_attempts)
                    return result
        except Exception as e:
            installation_attempts.append(f"pip install failed: {e}")
    
    # All methods failed, provide suggestions
    result["multiqc_install_output"] = "\n".join(installation_attempts)
    
    # Generate helpful suggestions based on what's available
    if "externally-managed-environment" in result["multiqc_install_output"]:
        if not result["pipx_available"] and result["brew_available"]:
            result["suggestions"].append("Install pipx via brew: brew install pipx && pipx install multiqc")
        elif not result["pipx_available"]:
            result["suggestions"].append("Install pipx: python3 -m pip install --user pipx && pipx install multiqc")
        result["suggestions"].append("Create virtual environment: python3 -m venv multiqc_env && source multiqc_env/bin/activate && pip install multiqc")
        result["suggestions"].append("Use --break-system-packages (not recommended): pip install multiqc --break-system-packages")
    else:
        if not result["pipx_available"] and result["brew_available"]:
            result["suggestions"].append("Install pipx via brew: brew install pipx && pipx install multiqc")
        elif not result["pipx_available"]:
            result["suggestions"].append("Install pipx: python3 -m pip install --user pipx && pipx install multiqc")
        if not result["brew_available"] and platform.system() == "Darwin":
            result["suggestions"].append("Install Homebrew: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        result["suggestions"].append("Manual installation: Visit https://multiqc.info/docs/getting_started/installation/")
    
    result["error"] = f"All installation methods failed. See suggestions for manual installation options."
    
    return result

def is_multiqc_installed() -> dict:
    """Check if MultiQC is installed on the system, return its path, status, and version."""
    result = {
        "multiqc_installed": False,
        "multiqc_path": None,
        "multiqc_version": None,
        "which_output": None,
        "python_available": False,
        "python_path": None,
        "python_version": None,
        "pip_available": False,
        "pip_path": None,
        "error": None
    }
    
    try:
        # Check MultiQC
        multiqc_path = shutil.which("multiqc")
        
        # If not found in PATH, check pipx installation location
        if not multiqc_path:
            pipx_bin_path = os.path.expanduser("~/.local/bin/multiqc")
            if os.path.exists(pipx_bin_path):
                multiqc_path = pipx_bin_path
                result["path_issue"] = True
                result["path_fix_suggestion"] = "Run 'pipx ensurepath' to add ~/.local/bin to PATH"
                
                # Automatically try to fix PATH if pipx is available
                pipx_path = shutil.which("pipx")
                if pipx_path:
                    try:
                        proc_path = subprocess.run([pipx_path, "ensurepath"], 
                                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                        result["path_fix_attempted"] = True
                        result["path_fix_output"] = proc_path.stdout + proc_path.stderr
                        result["path_fix_success"] = proc_path.returncode == 0
                        if proc_path.returncode == 0:
                            result["path_fix_message"] = "PATH fix attempted. You may need to restart your shell or run 'source ~/.zshrc'"
                    except Exception as e:
                        result["path_fix_error"] = str(e)
        
        result["multiqc_path"] = multiqc_path
        if multiqc_path:
            result["multiqc_installed"] = True
            # Try to get version
            try:
                proc = subprocess.run([multiqc_path, "--version"], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                result["multiqc_version"] = proc.stdout.strip() or proc.stderr.strip()
            except Exception as e:
                result["multiqc_version"] = f"Error getting version: {e}"
        
        # which output
        try:
            proc = subprocess.run(["which", "multiqc"], 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            result["which_output"] = proc.stdout.strip() or proc.stderr.strip()
        except Exception as e:
            result["which_output"] = f"Error running which: {e}"
        
        # Check Python
        python_path = shutil.which("python") or shutil.which("python3")
        result["python_path"] = python_path
        if python_path:
            result["python_available"] = True
            try:
                proc = subprocess.run([python_path, "--version"], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                result["python_version"] = proc.stdout.strip() or proc.stderr.strip()
            except Exception as e:
                result["python_version"] = f"Error getting version: {e}"
        
        # Check pip
        pip_path = shutil.which("pip") or shutil.which("pip3")
        result["pip_path"] = pip_path
        if pip_path:
            result["pip_available"] = True
            
    except Exception as e:
        result["error"] = str(e)
    
    return result

def fix_multiqc_path() -> dict:
    """Fix MultiQC PATH issues by running pipx ensurepath and providing manual instructions."""
    result = {
        "path_fix_attempted": False,
        "path_fix_success": False,
        "path_fix_output": None,
        "manual_instructions": [],
        "error": None
    }
    
    # Check if pipx is available
    pipx_path = shutil.which("pipx")
    if not pipx_path:
        result["error"] = "pipx not found in PATH"
        result["manual_instructions"] = [
            "Add to your shell config file (~/.zshrc or ~/.bashrc):",
            'export PATH="$HOME/.local/bin:$PATH"',
            "Then run: source ~/.zshrc (or restart terminal)"
        ]
        return result
    
    # Try to run pipx ensurepath
    try:
        result["path_fix_attempted"] = True
        proc = subprocess.run([pipx_path, "ensurepath"], 
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        result["path_fix_output"] = proc.stdout + proc.stderr
        result["path_fix_success"] = proc.returncode == 0
        
        if proc.returncode == 0:
            result["message"] = "PATH fix attempted successfully"
        else:
            result["error"] = f"pipx ensurepath failed with return code {proc.returncode}"
        
        # Always provide manual instructions as backup
        shell = os.environ.get('SHELL', '/bin/bash')
        if 'zsh' in shell:
            config_file = "~/.zshrc"
        else:
            config_file = "~/.bashrc"
            
        result["manual_instructions"] = [
            f"If automatic fix didn't work, manually add to {config_file}:",
            'export PATH="$HOME/.local/bin:$PATH"',
            f"Then run: source {config_file}",
            "Or restart your terminal"
        ]
        
    except Exception as e:
        result["error"] = str(e)
        result["manual_instructions"] = [
            "Manual PATH fix required:",
            "Add to your shell config file (~/.zshrc or ~/.bashrc):",
            'export PATH="$HOME/.local/bin:$PATH"',
            "Then run: source ~/.zshrc (or restart terminal)"
        ]
    
    return result
