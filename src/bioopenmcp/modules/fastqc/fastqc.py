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

# Global dictionaries to track background FastQC processes
_fastqc_processes: Dict[str, Dict] = {}  # For serializable job info
_fastqc_process_objects: Dict[str, subprocess.Popen] = {}  # For process objects only

def fastqc(fastq_path: str, search_if_not_found: bool = True) -> str:
    """Runs FastQC on a FASTQ file and returns the path to the HTML report.
    Args:
        fastq_path: Full path to FASTQ file or just filename to search for
        search_if_not_found: If True, search for the file if full path doesn't exist
    """
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
    # Try to find FastQC in system
    fastqc_path = shutil.which("fastqc")
    if not fastqc_path:
        # Fallback paths
        conda_fastqc = "/opt/anaconda3/bin/fastqc"
        if os.path.exists(conda_fastqc):
            fastqc_path = conda_fastqc
        else:
            raise RuntimeError("FastQC not found. Please install FastQC.")
    # Check if the FastQC executable exists
    if not os.path.exists(fastqc_path):
        raise RuntimeError(f"FastQC not found at {fastqc_path}. Please check your installation.")
    output_dir = os.path.dirname(fastq_path)
    cmd = [fastqc_path, fastq_path, "--outdir", output_dir]
    # Set up environment with Java path - prioritize conda Java
    env = os.environ.copy()
    # Try conda Java first
    conda_java = "/opt/anaconda3/lib/jvm/bin/java"
    if os.path.exists(conda_java):
        java_executable = conda_java
        java_dir = "/opt/anaconda3/lib/jvm/bin"
        java_home = "/opt/anaconda3/lib/jvm"
    else:
        # Fallback to system Java
        java_executable = shutil.which("java")
        if java_executable and os.path.exists(java_executable):
            java_dir = os.path.dirname(java_executable)
            java_home = java_dir
        else:
            raise RuntimeError("Java not found. Please install Java (JRE) to run FastQC.")
    # Set Java environment variables
    env["JAVA_HOME"] = java_home
    env["PATH"] = f"{java_dir}:{env.get('PATH', '')}"
    # Run FastQC and capture output
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    # Check if the output file was created
    base = os.path.splitext(os.path.basename(fastq_path))[0]
    report_path = os.path.join(output_dir, f"{base}_fastqc.html")
    if not os.path.exists(report_path):
        error_msg = result.stderr if result.stderr else "Unknown error"
        raise RuntimeError(f"FastQC failed to create report: {error_msg}")
    return report_path

def fastqc_background(fastq_path: str, job_id: Optional[str] = None, search_if_not_found: bool = True) -> Dict:
    """Runs FastQC in the background and returns job information.
    Args:
        fastq_path: Full path to FASTQ file or just filename to search for
        job_id: Optional custom job ID. If not provided, will be auto-generated
        search_if_not_found: If True, search for the file if full path doesn't exist
    Returns:
        Dictionary containing job_id, status, and other job information
    """
    global _fastqc_processes
    
    # Generate job ID if not provided
    if job_id is None:
        base_name = os.path.splitext(os.path.basename(fastq_path))[0]
        job_id = f"fastqc_{base_name}_{int(time.time())}"
    
    # Check if job_id already exists
    if job_id in _fastqc_processes:
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
    
    # Try to find FastQC in system
    fastqc_path = shutil.which("fastqc")
    if not fastqc_path:
        # Fallback paths
        conda_fastqc = "/opt/anaconda3/bin/fastqc"
        if os.path.exists(conda_fastqc):
            fastqc_path = conda_fastqc
        else:
            raise RuntimeError("FastQC not found. Please install FastQC.")
    
    # Check if the FastQC executable exists
    if not os.path.exists(fastqc_path):
        raise RuntimeError(f"FastQC not found at {fastqc_path}. Please check your installation.")
    
    output_dir = os.path.dirname(fastq_path)
    cmd = [fastqc_path, fastq_path, "--outdir", output_dir]
    
    # Set up environment with Java path - prioritize conda Java
    env = os.environ.copy()
    # Try conda Java first
    conda_java = "/opt/anaconda3/lib/jvm/bin/java"
    if os.path.exists(conda_java):
        java_executable = conda_java
        java_dir = "/opt/anaconda3/lib/jvm/bin"
        java_home = "/opt/anaconda3/lib/jvm"
    else:
        # Fallback to system Java
        java_executable = shutil.which("java")
        if java_executable and os.path.exists(java_executable):
            java_dir = os.path.dirname(java_executable)
            java_home = java_dir
        else:
            raise RuntimeError("Java not found. Please install Java (JRE) to run FastQC.")
    
    # Set Java environment variables
    env["JAVA_HOME"] = java_home
    env["PATH"] = f"{java_dir}:{env.get('PATH', '')}"
    
    # Initialize job info
    job_info = {
        "job_id": job_id,
        "fastq_path": fastq_path,
        "output_dir": output_dir,
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
    
    def run_fastqc():
        """Background function to run FastQC"""
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
            report_path = os.path.join(output_dir, f"{base}_fastqc.html")
            
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
    thread = threading.Thread(target=run_fastqc)
    thread.daemon = True
    thread.start()
    
    # Store job info
    _fastqc_processes[job_id] = job_info
    
    return {
        "job_id": job_id,
        "status": "started",
        "message": f"FastQC job '{job_id}' started in background"
    }

def get_fastqc_status(job_id: str) -> Dict:
    """Get the status of a background FastQC job.
    Args:
        job_id: The job ID to check
    Returns:
        Dictionary containing job status and information
    """
    global _fastqc_processes
    
    if job_id not in _fastqc_processes:
        return {
            "job_id": job_id,
            "status": "not_found",
            "error": f"Job ID '{job_id}' not found"
        }
    
    job_info = _fastqc_processes[job_id]
    
    # Create a serializable copy of job info (excluding the process object)
    serializable_info = {
        "job_id": job_info["job_id"],
        "fastq_path": job_info["fastq_path"],
        "output_dir": job_info["output_dir"],
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

def list_fastqc_jobs() -> Dict:
    """List all background FastQC jobs and their statuses.
    Returns:
        Dictionary containing all job information
    """
    global _fastqc_processes
    
    jobs = {}
    for job_id, job_info in _fastqc_processes.items():
        jobs[job_id] = get_fastqc_status(job_id)
    
    return {
        "total_jobs": len(jobs),
        "jobs": jobs
    }

def stop_fastqc_job(job_id: str) -> Dict:
    """Stop a running FastQC job.
    Args:
        job_id: The job ID to stop
    Returns:
        Dictionary containing stop operation result
    """
    global _fastqc_processes
    
    if job_id not in _fastqc_processes:
        return {
            "job_id": job_id,
            "status": "not_found",
            "error": f"Job ID '{job_id}' not found"
        }
    
    job_info = _fastqc_processes[job_id]
    
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

def cleanup_fastqc_jobs(completed_only: bool = True) -> Dict:
    """Clean up completed or failed FastQC jobs from memory.
    Args:
        completed_only: If True, only remove completed/failed jobs. If False, remove all jobs.
    Returns:
        Dictionary containing cleanup results
    """
    global _fastqc_processes
    
    jobs_to_remove = []
    for job_id, job_info in _fastqc_processes.items():
        if completed_only:
            if job_info["status"] in ["completed", "failed", "stopped"]:
                jobs_to_remove.append(job_id)
        else:
            jobs_to_remove.append(job_id)
    
    for job_id in jobs_to_remove:
        del _fastqc_processes[job_id]
    
    return {
        "removed_jobs": len(jobs_to_remove),
        "remaining_jobs": len(_fastqc_processes),
        "removed_job_ids": jobs_to_remove
    }

def install_fastqc() -> dict:
    """Install Java and FastQC if not present. Returns a summary of actions taken and installation status."""
    import shutil
    import subprocess
    result = {
        "java_installed": False,
        "java_install_attempted": False,
        "java_install_output": None,
        "fastqc_installed": False,
        "fastqc_install_attempted": False,
        "fastqc_install_output": None,
        "error": None
    }
    # Check Java
    java_path = shutil.which("java")
    if java_path:
        result["java_installed"] = True
    else:
        result["java_install_attempted"] = True
        # Try to install Java (OpenJDK) using brew on macOS
        if platform.system() == "Darwin":
            try:
                proc = subprocess.run(["brew", "install", "openjdk"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                result["java_install_output"] = proc.stdout + "\n" + proc.stderr
                # Re-check
                java_path = shutil.which("java")
                if java_path:
                    result["java_installed"] = True
            except Exception as e:
                result["error"] = f"Failed to install Java: {e}"
        else:
            result["error"] = "Automatic Java installation is only supported on macOS (Darwin) with Homebrew. Please install Java manually."
            return result
    # Check FastQC
    fastqc_path = shutil.which("fastqc")
    if fastqc_path:
        result["fastqc_installed"] = True
    else:
        result["fastqc_install_attempted"] = True
        # Try to install FastQC using brew on macOS
        if platform.system() == "Darwin":
            try:
                proc = subprocess.run(["brew", "install", "fastqc"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                result["fastqc_install_output"] = proc.stdout + "\n" + proc.stderr
                # Re-check
                fastqc_path = shutil.which("fastqc")
                if fastqc_path:
                    result["fastqc_installed"] = True
            except Exception as e:
                result["error"] = f"Failed to install FastQC: {e}"
        else:
            result["error"] = "Automatic FastQC installation is only supported on macOS (Darwin) with Homebrew. Please install FastQC manually."
    return result

def is_fastqc_installed() -> dict:
    """Check if fastqc is installed on the system, return its path, status, output of 'which fastqc', version check, and Java diagnostics."""
    import shutil
    import subprocess
    result = {
        "fastqc_installed": False,
        "fastqc_path": None,
        "fastqc_version": None,
        "which_output": None,
        "java_installed": False,
        "java_path": None,
        "java_version": None,
        "error": None
    }
    try:
        fastqc_path = shutil.which("fastqc")
        result["fastqc_path"] = fastqc_path
        if fastqc_path:
            result["fastqc_installed"] = True
            # Try to get version
            try:
                proc = subprocess.run([fastqc_path, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                result["fastqc_version"] = proc.stdout.strip() or proc.stderr.strip()
            except Exception as e:
                result["fastqc_version"] = f"Error getting version: {e}"
        # which output
        try:
            proc = subprocess.run(["which", "fastqc"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            result["which_output"] = proc.stdout.strip() or proc.stderr.strip()
        except Exception as e:
            result["which_output"] = f"Error running which: {e}"
        # Check Java
        java_path = shutil.which("java")
        result["java_path"] = java_path
        if java_path:
            result["java_installed"] = True
            try:
                proc = subprocess.run([java_path, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                # Java version is usually in stderr
                result["java_version"] = proc.stderr.strip() or proc.stdout.strip()
            except Exception as e:
                result["java_version"] = f"Error getting version: {e}"
    except Exception as e:
        result["error"] = str(e)
    return result 