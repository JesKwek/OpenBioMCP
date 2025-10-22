import shutil
import subprocess
import sys
import os
import threading
import time
import json
import datetime
from typing import Dict, Optional, List

# Global dictionaries to track background cutadapt processes
_cutadapt_processes: Dict[str, Dict] = {}  # For serializable job info
_cutadapt_process_objects: Dict[str, subprocess.Popen] = {}  # For process objects only

def is_cutadapt_installed() -> dict:
    """Check if cutadapt is installed, return its path, version, and status."""
    result = {
        "cutadapt_installed": False,
        "cutadapt_path": None,
        "cutadapt_version": None,
        "which_output": None,
        "error": None
    }
    try:
        cutadapt_path = shutil.which("cutadapt")
        result["cutadapt_path"] = cutadapt_path
        if cutadapt_path:
            result["cutadapt_installed"] = True
            try:
                proc = subprocess.run([cutadapt_path, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                result["cutadapt_version"] = proc.stdout.strip() or proc.stderr.strip()
            except Exception as e:
                result["cutadapt_version"] = f"Error getting version: {e}"
        try:
            proc = subprocess.run(["which", "cutadapt"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            result["which_output"] = proc.stdout.strip() or proc.stderr.strip()
        except Exception as e:
            result["which_output"] = f"Error running which: {e}"
    except Exception as e:
        result["error"] = str(e)
    return result

def install_cutadapt() -> dict:
    """Install cutadapt using pip if not present. Returns a summary of actions taken and installation status."""
    result = {
        "cutadapt_installed": False,
        "cutadapt_install_attempted": False,
        "cutadapt_install_output": None,
        "cutadapt_version": None,
        "error": None
    }
    cutadapt_path = shutil.which("cutadapt")
    if cutadapt_path:
        result["cutadapt_installed"] = True
        try:
            proc = subprocess.run([cutadapt_path, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            result["cutadapt_version"] = proc.stdout.strip() or proc.stderr.strip()
        except Exception as e:
            result["cutadapt_version"] = f"Error getting version: {e}"
        return result
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
        result["error"] = str(e)
    return result

def run_cutadapt(args: list, input_file: str = None, output_file: str = None) -> dict:
    """Run cutadapt with the given arguments. Optionally specify input and output files. Returns output and status."""
    result = {
        "success": False,
        "command": None,
        "stdout": None,
        "stderr": None,
        "output_file": output_file,
        "error": None
    }
    cutadapt_path = shutil.which("cutadapt")
    if not cutadapt_path:
        result["error"] = "cutadapt not found. Please install cutadapt."
        return result
    cmd = [cutadapt_path] + args
    if input_file:
        cmd += ["-o", output_file, input_file] if output_file else [input_file]
    result["command"] = " ".join(cmd)
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        result["stdout"] = proc.stdout
        result["stderr"] = proc.stderr
        result["success"] = proc.returncode == 0
    except Exception as e:
        result["error"] = str(e)
    return result

def cutadapt_background(args: List[str], job_id: Optional[str] = None, input_file: str = None, output_file: str = None) -> Dict:
    """Runs cutadapt in the background and returns job information.
    Args:
        args: List of cutadapt arguments
        job_id: Optional custom job ID. If not provided, will be auto-generated
        input_file: Input file path
        output_file: Output file path
    Returns:
        Dictionary containing job_id, status, and other job information
    """
    global _cutadapt_processes
    
    # Generate job ID if not provided
    if job_id is None:
        base_name = os.path.splitext(os.path.basename(input_file))[0] if input_file else "cutadapt"
        job_id = f"cutadapt_{base_name}_{int(time.time())}"
    
    # Check if job_id already exists
    if job_id in _cutadapt_processes:
        raise RuntimeError(f"Job ID '{job_id}' already exists. Please use a different job ID.")
    
    # Check if cutadapt is installed
    cutadapt_path = shutil.which("cutadapt")
    if not cutadapt_path:
        raise RuntimeError("cutadapt not found. Please install cutadapt.")
    
    # Build command
    cmd = [cutadapt_path] + args
    if input_file:
        if output_file:
            cmd += ["-o", output_file, input_file]
        else:
            cmd += [input_file]
    
    # Initialize job info
    job_info = {
        "job_id": job_id,
        "command": " ".join(cmd),
        "args": args,
        "input_file": input_file,
        "output_file": output_file,
        "status": "starting",
        "start_time": time.time(),
        "end_time": None,
        "process": None,
        "stdout": "",
        "stderr": "",
        "return_code": None,
        "error": None
    }
    
    def run_cutadapt_background():
        """Background function to run cutadapt"""
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
            
            if process.returncode == 0:
                job_info["status"] = "completed"
            else:
                job_info["status"] = "failed"
                job_info["error"] = stderr if stderr else "Unknown error"
                
        except Exception as e:
            job_info["status"] = "failed"
            job_info["error"] = str(e)
            job_info["end_time"] = time.time()
    
    # Start the background thread
    thread = threading.Thread(target=run_cutadapt_background)
    thread.daemon = True
    thread.start()
    
    # Store job info
    _cutadapt_processes[job_id] = job_info
    
    return {
        "job_id": job_id,
        "status": "started",
        "message": f"cutadapt job '{job_id}' started in background"
    }

def get_cutadapt_status(job_id: str) -> Dict:
    """Get the status of a background cutadapt job.
    Args:
        job_id: The job ID to check
    Returns:
        Dictionary containing job status and information
    """
    global _cutadapt_processes
    
    if job_id not in _cutadapt_processes:
        return {
            "job_id": job_id,
            "status": "not_found",
            "error": f"Job ID '{job_id}' not found"
        }
    
    job_info = _cutadapt_processes[job_id]
    
    # Create a serializable copy of job info (excluding the process object)
    serializable_info = {
        "job_id": job_info["job_id"],
        "command": job_info["command"],
        "args": job_info["args"],
        "input_file": job_info["input_file"],
        "output_file": job_info["output_file"],
        "status": job_info["status"],
        "start_time": job_info["start_time"],
        "end_time": job_info["end_time"],
        "stdout": job_info["stdout"],
        "stderr": job_info["stderr"],
        "return_code": job_info["return_code"],
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

def list_cutadapt_jobs() -> Dict:
    """List all background cutadapt jobs and their statuses.
    Returns:
        Dictionary containing all job information
    """
    global _cutadapt_processes
    
    jobs = {}
    for job_id, job_info in _cutadapt_processes.items():
        jobs[job_id] = get_cutadapt_status(job_id)
    
    return {
        "total_jobs": len(jobs),
        "jobs": jobs
    }

def stop_cutadapt_job(job_id: str) -> Dict:
    """Stop a running cutadapt job.
    Args:
        job_id: The job ID to stop
    Returns:
        Dictionary containing stop operation result
    """
    global _cutadapt_processes
    
    if job_id not in _cutadapt_processes:
        return {
            "job_id": job_id,
            "status": "not_found",
            "error": f"Job ID '{job_id}' not found"
        }
    
    job_info = _cutadapt_processes[job_id]
    
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

def cleanup_cutadapt_jobs(completed_only: bool = True) -> Dict:
    """Clean up completed or failed cutadapt jobs from memory.
    Args:
        completed_only: If True, only remove completed/failed jobs. If False, remove all jobs.
    Returns:
        Dictionary containing cleanup results
    """
    global _cutadapt_processes
    
    jobs_to_remove = []
    for job_id, job_info in _cutadapt_processes.items():
        if completed_only:
            if job_info["status"] in ["completed", "failed", "stopped"]:
                jobs_to_remove.append(job_id)
        else:
            jobs_to_remove.append(job_id)
    
    for job_id in jobs_to_remove:
        del _cutadapt_processes[job_id]
    
    return {
        "removed_jobs": len(jobs_to_remove),
        "remaining_jobs": len(_cutadapt_processes),
        "removed_job_ids": jobs_to_remove
    } 