import os
import glob
import shutil
import subprocess
import platform
import threading
import time
import json
import datetime
from typing import Dict, Optional
from bioopenmcp.modules.searching_file.searching_file import find_fastq_files

# Global dictionaries to track background trim_galore processes
_trim_galore_processes: Dict[str, Dict] = {}  # For serializable job info
_trim_galore_process_objects: Dict[str, subprocess.Popen] = {}  # For process objects only

def trim_galore(fastq_path: str, search_if_not_found: bool = True, extra_args: str = "") -> str:
    """Runs Trim Galore on a FASTQ file and returns the path to the trimmed file or report.
    Args:
        fastq_path: Full path to FASTQ file or just filename to search for
        search_if_not_found: If True, search for the file if full path doesn't exist
        extra_args: Additional command-line arguments for Trim Galore
    """
    if not os.path.exists(fastq_path) and search_if_not_found:
        found_files = find_fastq_files(fastq_path)
        if not found_files:
            raise RuntimeError(f"Could not find FASTQ file: {fastq_path}")
        elif len(found_files) == 1:
            fastq_path = found_files[0]
        else:
            fastq_path = found_files[0]
    trim_galore_path = shutil.which("trim_galore")
    if not trim_galore_path:
        conda_trim_galore = "/opt/anaconda3/bin/trim_galore"
        if os.path.exists(conda_trim_galore):
            trim_galore_path = conda_trim_galore
        else:
            raise RuntimeError("Trim Galore not found. Please install Trim Galore.")
    if not os.path.exists(trim_galore_path):
        raise RuntimeError(f"Trim Galore not found at {trim_galore_path}. Please check your installation.")
    output_dir = os.path.dirname(fastq_path)
    cmd = [trim_galore_path, fastq_path, "--output_dir", output_dir]
    if extra_args:
        cmd.extend(extra_args.split())
    env = os.environ.copy()
    # Java is not required for Trim Galore, but Python and cutadapt are dependencies
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    # Look for output file (Trim Galore appends _trimmed.fq or _val_1.fq, etc.)
    base = os.path.splitext(os.path.basename(fastq_path))[0]
    trimmed_files = glob.glob(os.path.join(output_dir, f"{base}*_trimmed.f*q*"))
    if not trimmed_files:
        trimmed_files = glob.glob(os.path.join(output_dir, f"{base}*_val_1.f*q*"))
    if not trimmed_files:
        error_msg = result.stderr if result.stderr else "Unknown error"
        raise RuntimeError(f"Trim Galore failed to create trimmed file: {error_msg}")
    return trimmed_files[0]

def trim_galore_background(fastq_path: str, job_id: Optional[str] = None, search_if_not_found: bool = True, extra_args: str = "") -> Dict:
    """Runs Trim Galore in the background and returns job information.
    Args:
        fastq_path: Full path to FASTQ file or just filename to search for
        job_id: Optional custom job ID. If not provided, will be auto-generated
        search_if_not_found: If True, search for the file if full path doesn't exist
        extra_args: Additional command-line arguments for Trim Galore
    Returns:
        Dictionary containing job_id, status, and other job information
    """
    global _trim_galore_processes
    
    # Generate job ID if not provided
    if job_id is None:
        base_name = os.path.splitext(os.path.basename(fastq_path))[0]
        job_id = f"trim_galore_{base_name}_{int(time.time())}"
    
    # Check if job_id already exists
    if job_id in _trim_galore_processes:
        raise RuntimeError(f"Job ID '{job_id}' already exists. Please use a different job ID.")
    
    # Check if the provided path exists
    if not os.path.exists(fastq_path) and search_if_not_found:
        # Try to find the file by name
        found_files = find_fastq_files(fastq_path)
        if not found_files:
            raise RuntimeError(f"Could not find FASTQ file: {fastq_path}")
        elif len(found_files) == 1:
            fastq_path = found_files[0]
        else:
            # Multiple files found, use the first one for now
            fastq_path = found_files[0]
    
    # Try to find Trim Galore in system
    trim_galore_path = shutil.which("trim_galore")
    if not trim_galore_path:
        conda_trim_galore = "/opt/anaconda3/bin/trim_galore"
        if os.path.exists(conda_trim_galore):
            trim_galore_path = conda_trim_galore
        else:
            raise RuntimeError("Trim Galore not found. Please install Trim Galore.")
    
    # Check if the Trim Galore executable exists
    if not os.path.exists(trim_galore_path):
        raise RuntimeError(f"Trim Galore not found at {trim_galore_path}. Please check your installation.")
    
    output_dir = os.path.dirname(fastq_path)
    cmd = [trim_galore_path, fastq_path, "--output_dir", output_dir]
    if extra_args:
        cmd.extend(extra_args.split())
    
    # Set up environment
    env = os.environ.copy()
    
    # Initialize job info
    job_info = {
        "job_id": job_id,
        "fastq_path": fastq_path,
        "output_dir": output_dir,
        "extra_args": extra_args,
        "command": " ".join(cmd),
        "status": "starting",
        "start_time": time.time(),
        "end_time": None,
        "process": None,
        "stdout": "",
        "stderr": "",
        "return_code": None,
        "trimmed_file_path": None,
        "error": None
    }
    
    def run_trim_galore_background():
        """Background function to run Trim Galore"""
        try:
            job_info["status"] = "running"
            # Start the process
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                env=env
            )
            job_info["process"] = process
            
            # Wait for completion
            stdout, stderr = process.communicate()
            job_info["stdout"] = stdout
            job_info["stderr"] = stderr
            job_info["return_code"] = process.returncode
            job_info["end_time"] = time.time()
            
            # Check if the output file was created
            base = os.path.splitext(os.path.basename(fastq_path))[0]
            trimmed_files = glob.glob(os.path.join(output_dir, f"{base}*_trimmed.f*q*"))
            if not trimmed_files:
                trimmed_files = glob.glob(os.path.join(output_dir, f"{base}*_val_1.f*q*"))
            
            if process.returncode == 0 and trimmed_files:
                job_info["status"] = "completed"
                job_info["trimmed_file_path"] = trimmed_files[0]
            else:
                job_info["status"] = "failed"
                job_info["error"] = stderr if stderr else "Unknown error"
                
        except Exception as e:
            job_info["status"] = "failed"
            job_info["error"] = str(e)
            job_info["end_time"] = time.time()
    
    # Start the background thread
    thread = threading.Thread(target=run_trim_galore_background)
    thread.daemon = True
    thread.start()
    
    # Store job info
    _trim_galore_processes[job_id] = job_info
    
    return {
        "job_id": job_id,
        "status": "started",
        "message": f"Trim Galore job '{job_id}' started in background"
    }

def get_trim_galore_status(job_id: str) -> Dict:
    """Get the status of a background Trim Galore job.
    Args:
        job_id: The job ID to check
    Returns:
        Dictionary containing job status and information
    """
    global _trim_galore_processes
    
    if job_id not in _trim_galore_processes:
        return {
            "job_id": job_id,
            "status": "not_found",
            "error": f"Job ID '{job_id}' not found"
        }
    
    job_info = _trim_galore_processes[job_id]
    
    # Create a serializable copy of job info (excluding the process object)
    serializable_info = {
        "job_id": job_info["job_id"],
        "fastq_path": job_info["fastq_path"],
        "output_dir": job_info["output_dir"],
        "extra_args": job_info["extra_args"],
        "command": job_info["command"],
        "status": job_info["status"],
        "start_time": job_info["start_time"],
        "end_time": job_info["end_time"],
        "stdout": job_info["stdout"],
        "stderr": job_info["stderr"],
        "return_code": job_info["return_code"],
        "trimmed_file_path": job_info["trimmed_file_path"],
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

def list_trim_galore_jobs() -> Dict:
    """List all background Trim Galore jobs and their statuses.
    Returns:
        Dictionary containing all job information
    """
    global _trim_galore_processes
    
    jobs = {}
    for job_id, job_info in _trim_galore_processes.items():
        jobs[job_id] = get_trim_galore_status(job_id)
    
    return {
        "total_jobs": len(jobs),
        "jobs": jobs
    }

def stop_trim_galore_job(job_id: str) -> Dict:
    """Stop a running Trim Galore job.
    Args:
        job_id: The job ID to stop
    Returns:
        Dictionary containing stop operation result
    """
    global _trim_galore_processes
    
    if job_id not in _trim_galore_processes:
        return {
            "job_id": job_id,
            "status": "not_found",
            "error": f"Job ID '{job_id}' not found"
        }
    
    job_info = _trim_galore_processes[job_id]
    
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

def cleanup_trim_galore_jobs(completed_only: bool = True) -> Dict:
    """Clean up completed or failed Trim Galore jobs from memory.
    Args:
        completed_only: If True, only remove completed/failed jobs. If False, remove all jobs.
    Returns:
        Dictionary containing cleanup results
    """
    global _trim_galore_processes
    
    jobs_to_remove = []
    for job_id, job_info in _trim_galore_processes.items():
        if completed_only:
            if job_info["status"] in ["completed", "failed", "stopped"]:
                jobs_to_remove.append(job_id)
        else:
            jobs_to_remove.append(job_id)
    
    for job_id in jobs_to_remove:
        del _trim_galore_processes[job_id]
    
    return {
        "removed_jobs": len(jobs_to_remove),
        "remaining_jobs": len(_trim_galore_processes),
        "removed_job_ids": jobs_to_remove
    }

def install_trim_galore() -> dict:
    """Install Trim Galore if not present. Also installs cutadapt if missing. Returns a summary of actions taken and installation status."""
    import shutil
    import subprocess
    import os
    import sys
    result = {
        "trim_galore_installed": False,
        "trim_galore_install_attempted": False,
        "trim_galore_install_output": None,
        "cutadapt_installed": False,
        "cutadapt_version": None,
        "cutadapt_install_attempted": False,
        "cutadapt_install_output": None,
        "fastqc_installed": False,
        "fastqc_version": None,
        "error": None
    }
    # Check for cutadapt
    cutadapt_path = shutil.which("cutadapt")
    if cutadapt_path:
        result["cutadapt_installed"] = True
        try:
            proc = subprocess.run([cutadapt_path, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            result["cutadapt_version"] = proc.stdout.strip() or proc.stderr.strip()
        except Exception as e:
            result["cutadapt_version"] = f"Error getting version: {e}"
    else:
        result["cutadapt_install_attempted"] = True
        try:
            proc = subprocess.run([sys.executable, "-m", "pip", "install", "cutadapt"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            result["cutadapt_install_output"] = proc.stdout + "\n" + proc.stderr
            cutadapt_path = shutil.which("cutadapt")
            if cutadapt_path:
                result["cutadapt_installed"] = True
                try:
                    proc = subprocess.run([cutadapt_path, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    result["cutadapt_version"] = proc.stdout.strip() or proc.stderr.strip()
                except Exception as e:
                    result["cutadapt_version"] = f"Error getting version: {e}"
            else:
                result["cutadapt_installed"] = False
        except Exception as e:
            result["cutadapt_install_output"] = f"Failed to install cutadapt: {e}"
            result["cutadapt_installed"] = False
    # Check for fastqc
    fastqc_path = shutil.which("fastqc")
    if fastqc_path:
        result["fastqc_installed"] = True
        try:
            proc = subprocess.run([fastqc_path, "-v"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            result["fastqc_version"] = proc.stderr.strip() or proc.stdout.strip()
        except Exception as e:
            result["fastqc_version"] = f"Error getting version: {e}"
    else:
        result["fastqc_installed"] = False
    # Check if Trim Galore is already installed
    trim_galore_path = shutil.which("trim_galore")
    if trim_galore_path:
        result["trim_galore_installed"] = True
        return result
    # Manual install from GitHub
    result["trim_galore_install_attempted"] = True
    url = "https://github.com/FelixKrueger/TrimGalore/archive/0.6.10.tar.gz"
    tarball = "trim_galore.tar.gz"
    folder = "TrimGalore-0.6.10"
    def cleanup_tarball(path):
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
    # First attempt: download to current directory
    cleanup_tarball(tarball)
    try:
        curl_proc = subprocess.run(["curl", "-fsSL", url, "-o", tarball], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if curl_proc.returncode != 0:
            raise RuntimeError(f"curl failed: {curl_proc.stderr.strip()}")
        tar_proc = subprocess.run(["tar", "xvzf", tarball], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if tar_proc.returncode != 0:
            raise RuntimeError(f"tar failed: {tar_proc.stderr.strip()}")
        home_bin = os.path.expanduser("~/bin")
        if not os.path.exists(home_bin):
            os.makedirs(home_bin)
        src = os.path.abspath(os.path.join(folder, "trim_galore"))
        dst = os.path.join(home_bin, "trim_galore")
        if os.path.exists(src):
            if os.path.exists(dst):
                os.remove(dst)
            os.symlink(src, dst)
        result["trim_galore_install_output"] = f"Downloaded and extracted {url}, symlinked to {dst}"
        os.environ["PATH"] = f"{home_bin}:{os.environ.get('PATH', '')}"
        trim_galore_path = shutil.which("trim_galore")
        if trim_galore_path:
            result["trim_galore_installed"] = True
    except Exception as e1:
        # If curl fails due to write error, try /tmp
        cleanup_tarball(tarball)
        tmp_tarball = "/tmp/trim_galore.tar.gz"
        cleanup_tarball(tmp_tarball)
        try:
            curl_proc = subprocess.run(["curl", "-fsSL", url, "-o", tmp_tarball], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if curl_proc.returncode != 0:
                raise RuntimeError(f"curl to /tmp failed: {curl_proc.stderr.strip()}")
            tar_proc = subprocess.run(["tar", "xvzf", tmp_tarball, "-C", "/tmp"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if tar_proc.returncode != 0:
                raise RuntimeError(f"tar to /tmp failed: {tar_proc.stderr.strip()}")
            home_bin = os.path.expanduser("~/bin")
            if not os.path.exists(home_bin):
                os.makedirs(home_bin)
            src = os.path.abspath(os.path.join("/tmp", folder, "trim_galore"))
            dst = os.path.join(home_bin, "trim_galore")
            if os.path.exists(src):
                if os.path.exists(dst):
                    os.remove(dst)
                os.symlink(src, dst)
            result["trim_galore_install_output"] = f"Downloaded and extracted {url} to /tmp, symlinked to {dst}"
            os.environ["PATH"] = f"{home_bin}:{os.environ.get('PATH', '')}"
            trim_galore_path = shutil.which("trim_galore")
            if trim_galore_path:
                result["trim_galore_installed"] = True
        except Exception as e2:
            result["trim_galore_install_output"] = f"Manual install failed: {e1}; Retry to /tmp failed: {e2}"
            result["error"] = f"Manual install failed: {e1}; Retry to /tmp failed: {e2}"
    return result

def is_trim_galore_installed() -> dict:
    """Check if Trim Galore is installed on the system, return its path, status, output of 'which trim_galore', version check, and cutadapt diagnostics."""
    import shutil
    import subprocess
    result = {
        "trim_galore_installed": False,
        "trim_galore_path": None,
        "trim_galore_version": None,
        "which_output": None,
        "cutadapt_installed": False,
        "cutadapt_path": None,
        "cutadapt_version": None,
        "error": None
    }
    try:
        trim_galore_path = shutil.which("trim_galore")
        result["trim_galore_path"] = trim_galore_path
        if trim_galore_path:
            result["trim_galore_installed"] = True
            try:
                proc = subprocess.run([trim_galore_path, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                result["trim_galore_version"] = proc.stdout.strip() or proc.stderr.strip()
            except Exception as e:
                result["trim_galore_version"] = f"Error getting version: {e}"
        try:
            proc = subprocess.run(["which", "trim_galore"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            result["which_output"] = proc.stdout.strip() or proc.stderr.strip()
        except Exception as e:
            result["which_output"] = f"Error running which: {e}"
        cutadapt_path = shutil.which("cutadapt")
        result["cutadapt_path"] = cutadapt_path
        if cutadapt_path:
            result["cutadapt_installed"] = True
            try:
                proc = subprocess.run([cutadapt_path, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                result["cutadapt_version"] = proc.stdout.strip() or proc.stderr.strip()
            except Exception as e:
                result["cutadapt_version"] = f"Error getting version: {e}"
    except Exception as e:
        result["error"] = str(e)
    return result 