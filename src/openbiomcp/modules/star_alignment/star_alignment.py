import os
import shutil
import subprocess
import platform
import threading
import time
import datetime
from typing import Dict, Optional
from bioopenmcp.modules.searching_file.searching_file import find_fastq_files

# Global dictionaries to track background STAR processes
_star_processes: Dict[str, Dict] = {}  # For serializable job info
_star_process_objects: Dict[str, subprocess.Popen] = {}  # For process objects only

# Global variable to track wrapper scripts for cleanup
_wrapper_scripts = []

def _cleanup_wrapper_scripts():
    """Clean up any temporary wrapper scripts created."""
    global _wrapper_scripts
    for script in _wrapper_scripts:
        try:
            if os.path.exists(script):
                os.remove(script)
        except:
            pass
    _wrapper_scripts.clear()



def run_star_alignment(fastq_path: str, genome_dir: str, output_dir: str, fastq_path_2: str = None, search_if_not_found: bool = True) -> str:
    """Runs STAR alignment on a FASTQ file and returns the path to the output BAM file.
    Args:
        fastq_path: Full path to FASTQ file or just filename to search for (read 1 for paired-end)
        genome_dir: Path to the STAR genome directory
        output_dir: Directory to write STAR output
        fastq_path_2: Optional path to second FASTQ file for paired-end reads
        search_if_not_found: If True, search for the file if full path doesn't exist
    """
    if not os.path.exists(fastq_path) and search_if_not_found:
        found_files = find_fastq_files(fastq_path)
        if not found_files:
            raise RuntimeError(f"Could not find FASTQ file: {fastq_path}")
        fastq_path = found_files[0]
    
    # Validate second FASTQ file if provided (for paired-end reads)
    if fastq_path_2:
        if not os.path.exists(fastq_path_2) and search_if_not_found:
            found_files = find_fastq_files(fastq_path_2)
            if not found_files:
                raise RuntimeError(f"Could not find second FASTQ file: {fastq_path_2}")
            fastq_path_2 = found_files[0]
    
    star_path = shutil.which("STAR")
    if not star_path:
        # Try common install locations
        for path in ["/usr/local/bin/STAR", "/opt/anaconda3/bin/STAR"]:
            if os.path.exists(path):
                star_path = path
                break
        if not star_path:
            raise RuntimeError("STAR not found. Please install STAR or run install_star().")
    if not os.path.exists(star_path):
        raise RuntimeError(f"STAR not found at {star_path}. Please check your installation.")
    if not os.path.exists(genome_dir):
        raise RuntimeError(f"Genome directory not found: {genome_dir}")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    out_prefix = os.path.join(output_dir, "star_")
    
    # Build STAR command with support for paired-end reads
    cmd = [
        star_path,
        "--genomeDir", genome_dir,
        "--outFileNamePrefix", out_prefix,
        "--runThreadN", "4",
        "--outSAMtype", "BAM", "SortedByCoordinate"
    ]
    
    # Check if files are compressed and raise error
    if fastq_path.endswith('.gz'):
        raise RuntimeError(f"Compressed FASTQ file detected: {fastq_path}. Please unzip the file before running STAR alignment.")
    if fastq_path_2 and fastq_path_2.endswith('.gz'):
        raise RuntimeError(f"Compressed FASTQ file detected: {fastq_path_2}. Please unzip the file before running STAR alignment.")
    
    # Add read files (single-end or paired-end)
    if fastq_path_2:
        cmd.extend(["--readFilesIn", fastq_path, fastq_path_2])
    else:
        cmd.extend(["--readFilesIn", fastq_path])
        
    result = subprocess.run(cmd, capture_output=True, text=True)
    bam_path = out_prefix + "Aligned.sortedByCoord.out.bam"
    if not os.path.exists(bam_path):
        error_msg = result.stderr if result.stderr else "Unknown error"
        raise RuntimeError(f"STAR failed to create BAM: {error_msg}")
    return bam_path

def star_alignment_background(fastq_path: str, genome_dir: str, output_dir: str, job_id: Optional[str] = None, search_if_not_found: bool = True, threads: int = 4, fastq_path_2: str = None) -> Dict:
    """Runs STAR alignment in the background and returns job information.
    Args:
        fastq_path: Full path to FASTQ file or just filename to search for (read 1 for paired-end)
        genome_dir: Path to the STAR genome directory
        output_dir: Directory to write STAR output
        job_id: Optional custom job ID. If not provided, will be auto-generated
        search_if_not_found: If True, search for the file if full path doesn't exist
        threads: Number of threads to use for STAR alignment
        fastq_path_2: Optional path to second FASTQ file for paired-end reads
    Returns:
        Dictionary containing job_id, status, and other job information
    """
    global _star_processes
    
    # Generate job ID if not provided
    if job_id is None:
        base_name = os.path.splitext(os.path.basename(fastq_path))[0]
        if fastq_path_2:
            base_name_2 = os.path.splitext(os.path.basename(fastq_path_2))[0]
            job_id = f"star_paired_{base_name}_{base_name_2}_{int(time.time())}"
        else:
            job_id = f"star_single_{base_name}_{int(time.time())}"
    
    # Check if job_id already exists
    if job_id in _star_processes:
        raise RuntimeError(f"Job ID '{job_id}' already exists. Please use a different job ID.")
    
    # Validate inputs
    if not os.path.exists(fastq_path) and search_if_not_found:
        found_files = find_fastq_files(fastq_path)
        if not found_files:
            raise RuntimeError(f"Could not find FASTQ file: {fastq_path}")
        fastq_path = found_files[0]
    
    # Validate second FASTQ file if provided (for paired-end reads)
    if fastq_path_2:
        if not os.path.exists(fastq_path_2) and search_if_not_found:
            found_files = find_fastq_files(fastq_path_2)
            if not found_files:
                raise RuntimeError(f"Could not find second FASTQ file: {fastq_path_2}")
            fastq_path_2 = found_files[0]
    
    star_path = shutil.which("STAR")
    if not star_path:
        # Try common install locations
        for path in ["/usr/local/bin/STAR", "/opt/anaconda3/bin/STAR"]:
            if os.path.exists(path):
                star_path = path
                break
        if not star_path:
            raise RuntimeError("STAR not found. Please install STAR or run install_star().")
    
    if not os.path.exists(star_path):
        raise RuntimeError(f"STAR not found at {star_path}. Please check your installation.")
    
    if not os.path.exists(genome_dir):
        raise RuntimeError(f"Genome directory not found: {genome_dir}")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    out_prefix = os.path.join(output_dir, "star_")
    
    # Build STAR command with support for paired-end reads
    cmd = [
        star_path,
        "--genomeDir", genome_dir,
        "--outFileNamePrefix", out_prefix,
        "--runThreadN", str(threads),
        "--outSAMtype", "BAM", "SortedByCoordinate"
    ]
    
    # Check if files are compressed and raise error
    if fastq_path.endswith('.gz'):
        raise RuntimeError(f"Compressed FASTQ file detected: {fastq_path}. Please unzip the file before running STAR alignment.")
    if fastq_path_2 and fastq_path_2.endswith('.gz'):
        raise RuntimeError(f"Compressed FASTQ file detected: {fastq_path_2}. Please unzip the file before running STAR alignment.")
    
    # Add read files (single-end or paired-end)
    if fastq_path_2:
        cmd.extend(["--readFilesIn", fastq_path, fastq_path_2])
    else:
        cmd.extend(["--readFilesIn", fastq_path])
    
    # Initialize job info
    job_info = {
        "job_id": job_id,
        "fastq_path": fastq_path,
        "fastq_path_2": fastq_path_2,
        "is_paired_end": bool(fastq_path_2),
        "genome_dir": genome_dir,
        "output_dir": output_dir,
        "out_prefix": out_prefix,
        "threads": threads,
        "command": " ".join(cmd),
        "status": "starting",
        "start_time": time.time(),
        "end_time": None,
        "process": None,
        "stdout": "",
        "stderr": "",
        "return_code": None,
        "bam_path": None,
        "error": None
    }
    
    def run_star():
        """Background function to run STAR alignment"""
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
            _star_process_objects[job_id] = process
            
            # Wait for completion
            stdout, stderr = process.communicate()
            job_info["stdout"] = stdout
            job_info["stderr"] = stderr
            job_info["return_code"] = process.returncode
            job_info["end_time"] = time.time()
            
            # Check if the output BAM file was created
            bam_path = out_prefix + "Aligned.sortedByCoord.out.bam"
            
            if process.returncode == 0 and os.path.exists(bam_path):
                job_info["status"] = "completed"
                job_info["bam_path"] = bam_path
            else:
                job_info["status"] = "failed"
                job_info["error"] = stderr if stderr else "Unknown error"
                
        except Exception as e:
            job_info["status"] = "failed"
            job_info["error"] = str(e)
            job_info["end_time"] = time.time()
        finally:
            # Clean up process object reference
            if job_id in _star_process_objects:
                del _star_process_objects[job_id]
    
    # Start the background thread
    thread = threading.Thread(target=run_star)
    thread.daemon = True
    thread.start()
    
    # Store job info
    _star_processes[job_id] = job_info
    
    return {
        "job_id": job_id,
        "status": "started",
        "message": f"STAR alignment job '{job_id}' started in background"
    }

def get_star_status(job_id: str) -> Dict:
    """Get the status of a background STAR alignment job.
    Args:
        job_id: The job ID to check
    Returns:
        Dictionary containing job status and information
    """
    global _star_processes
    
    if job_id not in _star_processes:
        return {
            "job_id": job_id,
            "status": "not_found",
            "error": f"Job ID '{job_id}' not found"
        }
    
    job_info = _star_processes[job_id]
    
    # Create a serializable copy of job info (excluding the process object)
    serializable_info = {
        "job_id": job_info["job_id"],
        "fastq_path": job_info["fastq_path"],
        "fastq_path_2": job_info.get("fastq_path_2"),
        "is_paired_end": job_info.get("is_paired_end", False),
        "genome_dir": job_info["genome_dir"],
        "output_dir": job_info["output_dir"],
        "out_prefix": job_info["out_prefix"],
        "threads": job_info.get("threads", 4),
        "command": job_info["command"],
        "status": job_info["status"],
        "start_time": job_info["start_time"],
        "end_time": job_info["end_time"],
        "stdout": job_info["stdout"],
        "stderr": job_info["stderr"],
        "return_code": job_info["return_code"],
        "bam_path": job_info["bam_path"],
        "error": job_info["error"]
    }
    
    # Convert timestamps to readable format
    if serializable_info["start_time"]:
        start_dt = datetime.datetime.fromtimestamp(serializable_info["start_time"])
        serializable_info["start_time_readable"] = start_dt.strftime("%I:%M:%S %p on %B %d, %Y")
    
    if serializable_info["end_time"]:
        end_dt = datetime.datetime.fromtimestamp(serializable_info["end_time"])
        serializable_info["end_time_readable"] = end_dt.strftime("%I:%M:%S %p on %B %d, %Y")
        
        # Calculate runtime
        runtime_seconds = serializable_info["end_time"] - serializable_info["start_time"]
        serializable_info["runtime_seconds"] = runtime_seconds
        serializable_info["runtime_readable"] = f"{runtime_seconds:.1f} seconds"
    
    return serializable_info

def list_star_jobs() -> Dict:
    """List all background STAR alignment jobs and their statuses.
    Returns:
        Dictionary containing all job information
    """
    global _star_processes
    
    jobs = {}
    for job_id, job_info in _star_processes.items():
        jobs[job_id] = get_star_status(job_id)
    
    return {
        "total_jobs": len(jobs),
        "jobs": jobs
    }

def stop_star_job(job_id: str) -> Dict:
    """Stop a running STAR alignment job.
    Args:
        job_id: The job ID to stop
    Returns:
        Dictionary containing stop result
    """
    global _star_processes, _star_process_objects
    
    if job_id not in _star_processes:
        return {
            "job_id": job_id,
            "status": "not_found",
            "error": f"Job ID '{job_id}' not found"
        }
    
    job_info = _star_processes[job_id]
    
    if job_info["status"] not in ["starting", "running"]:
        return {
            "job_id": job_id,
            "status": "already_finished",
            "message": f"Job '{job_id}' is already {job_info['status']}"
        }
    
    # Stop the process
    if job_id in _star_process_objects:
        process = _star_process_objects[job_id]
        try:
            process.terminate()
            # Wait a bit for graceful termination
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't terminate gracefully
            process.kill()
            process.wait()
        except Exception as e:
            return {
                "job_id": job_id,
                "status": "stop_failed",
                "error": f"Failed to stop job: {e}"
            }
    
    # Update job status
    job_info["status"] = "stopped"
    job_info["end_time"] = time.time()
    
    return {
        "job_id": job_id,
        "status": "stopped",
        "message": f"Job '{job_id}' has been stopped"
    }

def cleanup_star_jobs(completed_only: bool = True) -> Dict:
    """Clean up completed or failed STAR alignment jobs from memory.
    Args:
        completed_only: If True, only remove completed/failed jobs. If False, remove all jobs.
    Returns:
        Dictionary containing cleanup result
    """
    global _star_processes, _star_process_objects
    
    removed_jobs = []
    remaining_jobs = []
    
    for job_id, job_info in list(_star_processes.items()):
        should_remove = False
        
        if completed_only:
            # Only remove completed, failed, or stopped jobs
            if job_info["status"] in ["completed", "failed", "stopped"]:
                should_remove = True
        else:
            # Remove all jobs
            should_remove = True
        
        if should_remove:
            removed_jobs.append(job_id)
            del _star_processes[job_id]
            if job_id in _star_process_objects:
                del _star_process_objects[job_id]
        else:
            remaining_jobs.append(job_id)
    
    return {
        "removed_jobs": len(removed_jobs),
        "remaining_jobs": len(remaining_jobs),
        "removed_job_ids": removed_jobs
    }

def install_star() -> dict:
    """Install STAR if not present. Uses Homebrew on macOS, package managers on Linux, or compiles from source as fallback. Returns a summary of actions taken and installation status."""
    import tempfile
    result = {
        "version": "0.0.1",
        "star_installed": False,
        "star_install_attempted": False,
        "star_install_output": "",
        "gcc_installed": False,
        "gcc_install_attempted": False,
        "gcc_install_output": None,
        "libomp_installed": False,
        "libomp_install_attempted": False,
        "libomp_install_output": None,
        "brew_installed": False,
        "dependencies_installed": False,
        "install_method": None,
        "error": None
    }
    
    # Check if STAR is already installed
    star_path = shutil.which("STAR")
    if star_path:
        result["star_installed"] = True
        result["install_method"] = "already_installed"
        return result
    
    system = platform.system()
    result["star_install_attempted"] = True
    
    # macOS installation using Homebrew
    if system == "Darwin":
        try:
            # Check if Homebrew is available
            brew_path = shutil.which("brew")
            if not brew_path:
                result["error"] = "Homebrew not found. Please install Homebrew first:\n/bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
                return result
            
            result["brew_installed"] = True
            result["star_install_output"] += "Found Homebrew at: " + brew_path + "\n"
            
            # Install dependencies first
            dependencies = ["libomp", "wget"]
            for dep in dependencies:
                result["star_install_output"] += f"\nInstalling dependency: {dep}\n"
                proc = subprocess.run(["brew", "install", dep], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                result["star_install_output"] += proc.stdout + "\n" + proc.stderr + "\n"
                
                if proc.returncode != 0 and "already installed" not in proc.stderr.lower():
                    result["star_install_output"] += f"Warning: Failed to install {dep}, but continuing...\n"
            
            result["dependencies_installed"] = True
            result["libomp_install_attempted"] = True
            
            # Try installing STAR via Homebrew
            result["star_install_output"] += "\nAttempting to install STAR via Homebrew...\n"
            
            # First try the bioconda tap
            proc = subprocess.run(["brew", "tap", "brewsci/bio"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            result["star_install_output"] += "Adding brewsci/bio tap:\n" + proc.stdout + "\n" + proc.stderr + "\n"
            
            # Try to install STAR from the bio tap
            proc = subprocess.run(["brew", "install", "brewsci/bio/star"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            result["star_install_output"] += "Installing STAR from brewsci/bio:\n" + proc.stdout + "\n" + proc.stderr + "\n"
            
            if proc.returncode == 0:
                result["star_installed"] = True
                result["install_method"] = "homebrew_brewsci"
                return result
            
            # If that fails, try the regular formula
            proc = subprocess.run(["brew", "install", "star"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            result["star_install_output"] += "Installing STAR from main tap:\n" + proc.stdout + "\n" + proc.stderr + "\n"
            
            if proc.returncode == 0:
                result["star_installed"] = True
                result["install_method"] = "homebrew_main"
                return result
            
            # Try conda if available
            conda_path = shutil.which("conda")
            if conda_path:
                result["star_install_output"] += "\nTrying conda installation...\n"
                proc = subprocess.run(["conda", "install", "-c", "bioconda", "star", "-y"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                result["star_install_output"] += proc.stdout + "\n" + proc.stderr + "\n"
                
                if proc.returncode == 0:
                    result["star_installed"] = True
                    result["install_method"] = "conda"
                    return result
            
            result["star_install_output"] += "\nHomebrew and conda installation failed, falling back to source compilation...\n"
            
        except Exception as e:
            result["star_install_output"] += f"\nHomebrew installation failed with exception: {e}\n"
            result["star_install_output"] += "Falling back to source compilation...\n"
    
    # Linux installation using package managers
    elif system == "Linux":
        try:
            # Try apt-get first (Ubuntu/Debian)
            if shutil.which("apt-get"):
                result["star_install_output"] += "Trying apt-get installation...\n"
                proc = subprocess.run(["sudo", "apt-get", "update"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                result["star_install_output"] += proc.stdout + "\n" + proc.stderr + "\n"
                
                proc = subprocess.run(["sudo", "apt-get", "install", "-y", "rna-star"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                result["star_install_output"] += proc.stdout + "\n" + proc.stderr + "\n"
                
                if proc.returncode == 0:
                    result["star_installed"] = True
                    result["install_method"] = "apt"
                    return result
            
            # Try yum (CentOS/RHEL)
            elif shutil.which("yum"):
                result["star_install_output"] += "Trying yum installation...\n"
                proc = subprocess.run(["sudo", "yum", "install", "-y", "STAR"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                result["star_install_output"] += proc.stdout + "\n" + proc.stderr + "\n"
                
                if proc.returncode == 0:
                    result["star_installed"] = True
                    result["install_method"] = "yum"
                    return result
            
            # Try conda if available
            conda_path = shutil.which("conda")
            if conda_path:
                result["star_install_output"] += "Trying conda installation...\n"
                proc = subprocess.run(["conda", "install", "-c", "bioconda", "star", "-y"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                result["star_install_output"] += proc.stdout + "\n" + proc.stderr + "\n"
                
                if proc.returncode == 0:
                    result["star_installed"] = True
                    result["install_method"] = "conda"
                    return result
            
            result["star_install_output"] += "Package manager installation failed, falling back to source compilation...\n"
            
        except Exception as e:
            result["star_install_output"] += f"Package manager installation failed with exception: {e}\n"
            result["star_install_output"] += "Falling back to source compilation...\n"
    
    # Source compilation fallback
    result["star_install_output"] += "\nAttempting source compilation...\n"
    
    # Check for required tools for compilation
    required_tools = ["wget", "tar", "make"]
    missing_tools = []
    for tool in required_tools:
        if not shutil.which(tool):
            missing_tools.append(tool)
    
    if missing_tools:
        result["error"] = f"Missing required tools for compilation: {', '.join(missing_tools)}. Please install them first."
        return result
    
    # Check if we have a C++ compiler
    gcc_path = shutil.which("g++")
    clang_path = shutil.which("clang++")
    
    if not gcc_path and not clang_path:
        result["error"] = "No C++ compiler found. Please install GCC or Clang."
        return result
    
    result["gcc_installed"] = bool(gcc_path)
    
    # Download and build STAR
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            os.chdir(tmpdir)
            
            result["star_install_output"] += f"Working in temporary directory: {tmpdir}\n"
            
            # Download STAR source
            url = "https://github.com/alexdobin/STAR/archive/2.7.11b.tar.gz"
            tar_file = "2.7.11b.tar.gz"
            
            result["star_install_output"] += f"Downloading STAR from {url}...\n"
            proc = subprocess.run(["wget", url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            result["star_install_output"] += proc.stdout + "\n" + proc.stderr + "\n"
            
            if proc.returncode != 0:
                result["error"] = f"Failed to download STAR: {proc.stderr}"
                return result
            
            # Extract the archive
            result["star_install_output"] += "Extracting archive...\n"
            proc = subprocess.run(["tar", "-xzf", tar_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            result["star_install_output"] += proc.stdout + "\n" + proc.stderr + "\n"
            
            if proc.returncode != 0:
                result["error"] = f"Failed to extract STAR: {proc.stderr}"
                return result
            
            src_dir = os.path.join(tmpdir, "STAR-2.7.11b", "source")
            os.chdir(src_dir)
            result["star_install_output"] += f"Changed to source directory: {src_dir}\n"
            
            # Determine the appropriate compiler and flags
            if system == "Darwin":
                # On macOS, use clang++ with proper OpenMP support
                compiler = clang_path if clang_path else "/usr/bin/clang++"
                result["star_install_output"] += f"Using compiler: {compiler}\n"
                
                # Check if libomp is available
                libomp_flags = ""
                if shutil.which("brew") and result["dependencies_installed"]:
                    # Get libomp path from brew
                    proc = subprocess.run(["brew", "--prefix", "libomp"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    if proc.returncode == 0:
                        libomp_prefix = proc.stdout.strip()
                        libomp_flags = f"-I{libomp_prefix}/include -L{libomp_prefix}/lib -lomp"
                        result["star_install_output"] += f"Using libomp flags: {libomp_flags}\n"
                    else:
                        result["star_install_output"] += "Warning: libomp not found via brew, compiling without OpenMP support\n"
                
                # Try different compilation strategies for macOS
                # Check if we have GCC from Homebrew (preferred for macOS compilation)
                gcc_homebrew_path = None
                if shutil.which("brew"):
                    try:
                        # Check for GCC versions commonly installed via Homebrew
                        for version in ["13", "12", "11", "10", "9", "8"]:
                            gcc_candidate = f"/usr/local/bin/g++-{version}"
                            if os.path.exists(gcc_candidate):
                                gcc_homebrew_path = gcc_candidate
                                break
                            # Also check /opt/homebrew for Apple Silicon Macs
                            gcc_candidate = f"/opt/homebrew/bin/g++-{version}"
                            if os.path.exists(gcc_candidate):
                                gcc_homebrew_path = gcc_candidate
                                break
                    except:
                        pass
                
                strategies = [
                    # Strategy 1: Use STARforMacStatic with Homebrew GCC (most reliable)
                    {
                        "name": "STARforMacStatic with Homebrew GCC",
                        "cmd": ["make", "STARforMacStatic", f"CXX={gcc_homebrew_path}"] if gcc_homebrew_path else None
                    },
                    # Strategy 2: Use STARforMacStatic with system clang++ and libomp
                    {
                        "name": "STARforMacStatic with clang++ and libomp",
                        "cmd": ["make", "STARforMacStatic", f"CXX={compiler}", f"CXXFLAGS_SIMD=-Xpreprocessor -fopenmp {libomp_flags}"] if libomp_flags else None
                    },
                    # Strategy 3: Regular STAR target with Homebrew GCC
                    {
                        "name": "STAR with Homebrew GCC",
                        "cmd": ["make", "STAR", f"CXX={gcc_homebrew_path}"] if gcc_homebrew_path else None
                    },
                    # Strategy 4: Regular STAR target with OpenMP flags
                    {
                        "name": "STAR with libomp",
                        "cmd": ["make", "STAR", f"CXX={compiler}", f"CXXFLAGS_SIMD=-Xpreprocessor -fopenmp {libomp_flags}"] if libomp_flags else None
                    },
                    # Strategy 5: Without OpenMP (fallback)
                    {
                        "name": "STAR without OpenMP",
                        "cmd": ["make", "STAR", f"CXX={compiler}", "CXXFLAGS_SIMD=-DNO_THREADS"]
                    }
                ]
                
                successful_strategy = None
                for strategy in strategies:
                    # Skip strategies that don't have valid commands
                    if strategy["cmd"] is None:
                        continue
                    
                    # Skip libomp strategies if libomp is not available
                    if not libomp_flags and "libomp" in strategy["name"]:
                        continue
                    
                    result["star_install_output"] += f"\nTrying strategy: {strategy['name']}\n"
                    result["star_install_output"] += f"Command: {' '.join(strategy['cmd'])}\n"
                    
                    proc = subprocess.run(strategy["cmd"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    result["star_install_output"] += proc.stdout + "\n" + proc.stderr + "\n"
                    
                    if proc.returncode == 0:
                        successful_strategy = strategy["name"]
                        result["star_install_output"] += f"SUCCESS: {strategy['name']} worked!\n"
                        break
                    else:
                        result["star_install_output"] += f"FAILED: {strategy['name']} failed\n"
                
                if not successful_strategy:
                    result["error"] = "All compilation strategies failed on macOS"
                    return result
                    
                result["successful_strategy"] = successful_strategy
                
            else:
                # On Linux, use g++
                compiler = gcc_path if gcc_path else "g++"
                result["star_install_output"] += f"Using compiler: {compiler}\n"
                
                make_cmd = ["make", "STAR", f"CXX={compiler}"]
                result["star_install_output"] += f"Command: {' '.join(make_cmd)}\n"
                
                proc = subprocess.run(make_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                result["star_install_output"] += proc.stdout + "\n" + proc.stderr + "\n"
                
                if proc.returncode != 0:
                    result["error"] = f"STAR compilation failed on Linux: {proc.stderr}"
                    return result
            
            # Check if STAR binary was created
            star_bin = os.path.join(src_dir, "STAR")
            if os.path.exists(star_bin):
                result["star_install_output"] += f"STAR binary created at: {star_bin}\n"
                
                # Copy STAR binary to /usr/local/bin
                install_dir = "/usr/local/bin"
                install_path = os.path.join(install_dir, "STAR")
                
                # Ensure /usr/local/bin exists
                os.makedirs(install_dir, exist_ok=True)
                
                # Copy the binary
                shutil.copy(star_bin, install_path)
                os.chmod(install_path, 0o755)
                
                result["star_install_output"] += f"STAR installed to: {install_path}\n"
                result["star_installed"] = True
                result["install_method"] = "source_compilation"
                
                # Verify installation
                proc = subprocess.run([install_path, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if proc.returncode == 0:
                    result["star_install_output"] += f"Installation verified. Version: {proc.stdout.strip()}\n"
                else:
                    result["star_install_output"] += f"Warning: Could not verify installation: {proc.stderr}\n"
                
            else:
                result["error"] = "STAR binary not found after compilation."
                return result
            
            # Return to original directory
            os.chdir(original_dir)
            
    except Exception as e:
        result["error"] = f"Failed to install STAR via source compilation: {e}"
        result["star_install_output"] += f"\nException occurred: {e}\n"
    
    return result

def uninstall_star() -> dict:
    """Uninstall STAR from the system.
    Returns:
        Dictionary containing uninstall status and actions taken
    """
    result = {
        "star_was_installed": False,
        "star_path": None,
        "installation_method": None,
        "uninstall_attempted": False,
        "uninstall_successful": False,
        "actions_taken": [],
        "error": None,
        "homebrew_uninstall_output": None,
        "manual_removal_output": None
    }
    
    try:
        # Check if STAR is currently installed
        star_path = shutil.which("STAR")
        result["star_path"] = star_path
        
        if not star_path:
            result["actions_taken"].append("STAR is not currently installed")
            result["uninstall_successful"] = True
            return result
        
        result["star_was_installed"] = True
        result["actions_taken"].append(f"Found STAR at: {star_path}")
        
        # Determine installation method
        if os.path.islink(star_path):
            # Check if it's a Homebrew symlink
            link_target = os.readlink(star_path)
            if "Cellar" in link_target or "homebrew" in link_target.lower():
                result["installation_method"] = "homebrew"
                result["actions_taken"].append("Detected Homebrew installation (symlink to Cellar)")
            else:
                result["installation_method"] = "symlink_unknown"
                result["actions_taken"].append(f"Detected symlink to: {link_target}")
        else:
            result["installation_method"] = "manual_or_compiled"
            result["actions_taken"].append("Detected manual installation or compiled binary")
        
        result["uninstall_attempted"] = True
        
        # Try Homebrew uninstall first
        if shutil.which("brew"):
            result["actions_taken"].append("Attempting Homebrew uninstall...")
            try:
                # Check if STAR is installed via Homebrew
                proc = subprocess.run(["brew", "list", "star"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if proc.returncode == 0:
                    result["actions_taken"].append("STAR found in Homebrew package list")
                    # Uninstall via Homebrew
                    proc = subprocess.run(["brew", "uninstall", "star"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    result["homebrew_uninstall_output"] = proc.stdout + "\n" + proc.stderr
                    
                    if proc.returncode == 0:
                        result["actions_taken"].append("Successfully uninstalled STAR via Homebrew")
                        result["uninstall_successful"] = True
                    else:
                        result["actions_taken"].append(f"Homebrew uninstall failed: {proc.stderr}")
                else:
                    result["actions_taken"].append("STAR not found in Homebrew package list")
            except Exception as e:
                result["actions_taken"].append(f"Homebrew uninstall failed with exception: {e}")
        
        # If Homebrew uninstall didn't work or STAR is still present, try manual removal
        if not result["uninstall_successful"] or shutil.which("STAR"):
            result["actions_taken"].append("Attempting manual removal...")
            
            # Common STAR installation paths
            common_paths = [
                "/usr/local/bin/STAR",
                "/opt/anaconda3/bin/STAR",
                "/usr/bin/STAR",
                "/opt/homebrew/bin/STAR"
            ]
            
            removed_files = []
            for path in common_paths:
                if os.path.exists(path):
                    try:
                        if os.path.islink(path):
                            os.unlink(path)
                            removed_files.append(f"Removed symlink: {path}")
                        else:
                            os.remove(path)
                            removed_files.append(f"Removed file: {path}")
                    except PermissionError:
                        try:
                            # Try with sudo (this will require user interaction)
                            proc = subprocess.run(["sudo", "rm", "-f", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                            if proc.returncode == 0:
                                removed_files.append(f"Removed file with sudo: {path}")
                            else:
                                result["actions_taken"].append(f"Failed to remove {path}: {proc.stderr}")
                        except Exception as e:
                            result["actions_taken"].append(f"Failed to remove {path}: {e}")
                    except Exception as e:
                        result["actions_taken"].append(f"Error removing {path}: {e}")
            
            if removed_files:
                result["actions_taken"].extend(removed_files)
                result["manual_removal_output"] = "\n".join(removed_files)
        
        # Final check
        final_star_path = shutil.which("STAR")
        if not final_star_path:
            result["uninstall_successful"] = True
            result["actions_taken"].append("✅ STAR successfully uninstalled - no longer found in PATH")
        else:
            result["uninstall_successful"] = False
            result["actions_taken"].append(f"⚠️  STAR still found at: {final_star_path}")
            result["error"] = f"Uninstall incomplete - STAR still accessible at {final_star_path}"
    
    except Exception as e:
        result["error"] = str(e)
        result["actions_taken"].append(f"Uninstall failed with exception: {e}")
    
    return result

def is_star_installed() -> dict:
    """Check if STAR is installed on the system, return its path, status, and version."""
    result = {
        "star_installed": False,
        "star_path": None,
        "star_version": None,
        "which_output": None,
        "installation_method": None,
        "is_symlink": False,
        "symlink_target": None,
        "gcc_installed": False,
        "gcc_path": None,
        "gcc_version": None,
        "error": None
    }
    try:
        star_path = shutil.which("STAR")
        result["star_path"] = star_path
        if star_path:
            result["star_installed"] = True
            
            # Check if it's a symlink and determine installation method
            if os.path.islink(star_path):
                result["is_symlink"] = True
                link_target = os.readlink(star_path)
                result["symlink_target"] = link_target
                
                if "Cellar" in link_target or "homebrew" in link_target.lower():
                    result["installation_method"] = "homebrew"
                elif "anaconda" in link_target or "conda" in link_target:
                    result["installation_method"] = "conda"
                else:
                    result["installation_method"] = "symlink_unknown"
            else:
                result["installation_method"] = "manual_or_compiled"
            
            try:
                proc = subprocess.run([star_path, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                result["star_version"] = proc.stdout.strip() or proc.stderr.strip()
            except Exception as e:
                result["star_version"] = f"Error getting version: {e}"
        proc = subprocess.run(["which", "STAR"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        result["which_output"] = proc.stdout.strip() or proc.stderr.strip()
        gcc_path = shutil.which("g++")
        result["gcc_path"] = gcc_path
        if gcc_path:
            result["gcc_installed"] = True
            try:
                proc = subprocess.run([gcc_path, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                result["gcc_version"] = proc.stdout.strip() or proc.stderr.strip()
            except Exception as e:
                result["gcc_version"] = f"Error getting version: {e}"
    except Exception as e:
        result["error"] = str(e)
        return result

def get_macos_manual_installation_guide() -> dict:
    """Get detailed manual installation instructions for STAR on macOS.
    Returns:
        Dictionary containing step-by-step manual installation guide
    """
    guide = {
        "title": "Manual STAR Installation for macOS",
        "overview": "This guide provides updated manual installation steps for STAR on macOS using the latest compilation methods.",
        "prerequisites": [
            "Homebrew installed (https://brew.sh/)",
            "Command line tools or Xcode installed",
            "At least 2GB free disk space"
        ],
        "methods": [
            {
                "name": "Method 1: Homebrew Installation (Recommended)",
                "description": "Install STAR using Homebrew package manager",
                "steps": [
                    {
                        "step": 1,
                        "action": "Install Homebrew (if not already installed)",
                        "command": '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"',
                        "description": "Install the Homebrew package manager"
                    },
                    {
                        "step": 2,
                        "action": "Add bioinformatics tap",
                        "command": "brew tap brewsci/bio",
                        "description": "Add the brewsci/bio tap which contains STAR"
                    },
                    {
                        "step": 3,
                        "action": "Install STAR",
                        "command": "brew install brewsci/bio/star",
                        "description": "Install STAR from the bioinformatics tap"
                    },
                    {
                        "step": 4,
                        "action": "Verify installation",
                        "command": "STAR --version",
                        "description": "Check that STAR is installed and accessible"
                    }
                ]
            },
            {
                "name": "Method 2: Manual Compilation (Updated Steps)",
                "description": "Compile STAR from source with proper macOS configuration",
                "steps": [
                    {
                        "step": 1,
                        "action": "Install dependencies",
                        "command": "brew install gcc wget",
                        "description": "Install GCC compiler and wget for downloading source"
                    },
                    {
                        "step": 2,
                        "action": "Download STAR source",
                        "command": "wget https://github.com/alexdobin/STAR/archive/2.7.11b.tar.gz",
                        "description": "Download the latest STAR source code"
                    },
                    {
                        "step": 3,
                        "action": "Extract source",
                        "command": "tar -xzf 2.7.11b.tar.gz",
                        "description": "Extract the downloaded archive"
                    },
                    {
                        "step": 4,
                        "action": "Navigate to source directory",
                        "command": "cd STAR-2.7.11b/source",
                        "description": "Change to the source code directory"
                    },
                    {
                        "step": 5,
                        "action": "Find GCC version",
                        "command": "ls /usr/local/bin/g++-* || ls /opt/homebrew/bin/g++-*",
                        "description": "Find the installed GCC version (e.g., g++-13, g++-12, etc.)"
                    },
                    {
                        "step": 6,
                        "action": "Compile STAR for macOS",
                        "command": "make STARforMacStatic CXX=/usr/local/bin/g++-13",
                        "description": "Compile STAR using the STARforMacStatic target (replace g++-13 with your version)"
                    },
                    {
                        "step": 7,
                        "action": "Install STAR binary",
                        "command": "sudo cp STAR /usr/local/bin/",
                        "description": "Copy the compiled STAR binary to system PATH"
                    },
                    {
                        "step": 8,
                        "action": "Make executable",
                        "command": "sudo chmod +x /usr/local/bin/STAR",
                        "description": "Ensure STAR binary is executable"
                    },
                    {
                        "step": 9,
                        "action": "Verify installation",
                        "command": "STAR --version",
                        "description": "Check that STAR is installed and accessible"
                    }
                ]
            },
            {
                "name": "Method 3: Alternative Git Clone Method",
                "description": "Clone from git repository instead of downloading tar.gz",
                "steps": [
                    {
                        "step": 1,
                        "action": "Install dependencies",
                        "command": "brew install gcc git",
                        "description": "Install GCC compiler and git"
                    },
                    {
                        "step": 2,
                        "action": "Clone STAR repository",
                        "command": "git clone https://github.com/alexdobin/STAR.git",
                        "description": "Clone the STAR repository from GitHub"
                    },
                    {
                        "step": 3,
                        "action": "Navigate to source directory",
                        "command": "cd STAR/source",
                        "description": "Change to the source code directory"
                    },
                    {
                        "step": 4,
                        "action": "Compile and install",
                        "command": "make STARforMacStatic CXX=/usr/local/bin/g++-13 && sudo cp STAR /usr/local/bin/",
                        "description": "Compile and install in one step (adjust GCC version as needed)"
                    }
                ]
            }
        ],
        "troubleshooting": {
            "common_issues": [
                {
                    "issue": "GCC not found",
                    "solution": "Run 'brew install gcc' and check installed versions with 'ls /usr/local/bin/g++-*'"
                },
                {
                    "issue": "Permission denied when copying to /usr/local/bin",
                    "solution": "Use 'sudo' prefix: 'sudo cp STAR /usr/local/bin/'"
                },
                {
                    "issue": "STAR command not found after installation",
                    "solution": "Check that /usr/local/bin is in your PATH: 'echo $PATH'"
                },
                {
                    "issue": "Compilation fails with linker errors",
                    "solution": "Try using different GCC versions or install libomp: 'brew install libomp'"
                },
                {
                    "issue": "Apple Silicon Mac compilation issues",
                    "solution": "Use /opt/homebrew paths instead of /usr/local and ensure you have ARM64 compatible GCC"
                }
            ],
            "system_specific": {
                "intel_mac": {
                    "gcc_path": "/usr/local/bin/g++-*",
                    "install_path": "/usr/local/bin/STAR",
                    "notes": "Standard Intel Mac compilation should work with Homebrew GCC"
                },
                "apple_silicon_mac": {
                    "gcc_path": "/opt/homebrew/bin/g++-*",
                    "install_path": "/usr/local/bin/STAR",
                    "notes": "May need to use /opt/homebrew paths for GCC and ensure ARM64 compatibility"
                }
            }
        },
        "verification": {
            "commands": [
                "STAR --version",
                "which STAR",
                "STAR --help"
            ],
            "expected_output": "Should show STAR version information and help text"
        },
        "notes": [
            "The STARforMacStatic target is specifically designed for macOS and creates a static binary",
            "GCC versions may vary (8, 9, 10, 11, 12, 13) - use the highest version available",
            "On Apple Silicon Macs, paths may be /opt/homebrew instead of /usr/local",
            "If compilation fails, the automated install_star() function will try multiple strategies"
        ]
    }
    
    return guide

def get_installation_instructions() -> dict:
    """Get step-by-step installation instructions for STAR based on the current system.
    Returns:
        Dictionary containing installation instructions and requirements
    """
    system_info = check_system_requirements()
    
    instructions = {
        "system": system_info["system"],
        "current_status": system_info,
        "steps": [],
        "estimated_time": "5-15 minutes",
        "difficulty": "Easy to Intermediate"
    }
    
    if system_info["star_installed"]:
        instructions["steps"].append({
            "step": 1,
            "action": "STAR is already installed",
            "command": None,
            "description": f"STAR is available at: {system_info['star_path']}"
        })
        return instructions
    
    if system_info["system"] == "Darwin":  # macOS
        instructions["steps"].extend([
            {
                "step": 1,
                "action": "Install Homebrew (if not already installed)",
                "command": '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"',
                "description": "Homebrew is the recommended package manager for macOS"
            },
            {
                "step": 2,
                "action": "Run the automated STAR installer",
                "command": "from bioopenmcp.modules.star_alignment.star_alignment import install_star; install_star()",
                "description": "This will automatically: 1) Install dependencies (libomp, wget), 2) Try Homebrew installation via brewsci/bio tap, 3) Fall back to conda if available, 4) Compile from source with proper OpenMP support if needed"
            }
        ])
        instructions["installation_methods"] = [
            "Homebrew via brewsci/bio tap (preferred)",
            "Homebrew main tap",
            "Conda/Bioconda",
            "Source compilation with libomp support"
        ]
    else:  # Linux
        instructions["steps"].extend([
            {
                "step": 1,
                "action": "Run the automated STAR installer",
                "command": "from bioopenmcp.modules.star_alignment.star_alignment import install_star; install_star()",
                "description": "This will automatically: 1) Try package manager installation (apt-get, yum), 2) Try conda if available, 3) Fall back to source compilation if needed"
            }
        ])
        instructions["installation_methods"] = [
            "Package manager (apt-get for Ubuntu/Debian, yum for CentOS/RHEL)",
            "Conda/Bioconda", 
            "Source compilation"
        ]
    
    # Add manual installation options
    instructions["manual_options"] = {
        "homebrew_macos": {
            "command": "brew tap brewsci/bio && brew install brewsci/bio/star",
            "description": "Direct Homebrew installation on macOS"
        },
        "conda_any": {
            "command": "conda install -c bioconda star",
            "description": "Direct conda installation (any platform with conda)"
        },
        "apt_ubuntu": {
            "command": "sudo apt-get update && sudo apt-get install rna-star",
            "description": "Direct apt installation on Ubuntu/Debian"
        }
    }
    
    # Add troubleshooting steps
    if not system_info["installation_ready"]:
        instructions["troubleshooting"] = {
            "issues": system_info["recommendations"],
            "common_fixes": [
                "On macOS: Ensure Homebrew is installed and up to date",
                "On macOS: Install libomp with 'brew install libomp' for OpenMP support", 
                "On Linux: Install build-essential with 'sudo apt-get install build-essential'",
                "Try updating your package manager before installation",
                "Check that you have sufficient disk space (>2GB for compilation)"
            ],
            "manual_installation": "If automated installation fails, you can manually install STAR from: https://github.com/alexdobin/STAR"
        }
    
    return instructions

def generate_star_genome_index(genome_dir: str, genome_fasta: str, gtf_file: str = None, 
                              sjdb_overhang: int = 99, threads: int = 8, 
                              search_if_not_found: bool = True) -> str:
    """Generate a STAR genome index for alignment.
    
    Args:
        genome_dir: Directory to store the genome index
        genome_fasta: Path to the genome FASTA file
        gtf_file: Optional path to GTF annotation file
        sjdb_overhang: Overhang for splice junction database (default: 99 for 100bp reads)
        threads: Number of threads to use for index generation
        search_if_not_found: If True, search for files if full path doesn't exist
        
    Returns:
        Path to the generated genome index directory
        
    Raises:
        RuntimeError: If STAR is not found or index generation fails
    """
    # Check if STAR is available
    star_path = shutil.which("STAR")
    if not star_path:
        # Try common install locations
        for path in ["/usr/local/bin/STAR", "/opt/anaconda3/bin/STAR"]:
            if os.path.exists(path):
                star_path = path
                break
        if not star_path:
            raise RuntimeError("STAR not found. Please install STAR or run install_star().")
    
    if not os.path.exists(star_path):
        raise RuntimeError(f"STAR not found at {star_path}. Please check your installation.")
    
    # Validate input files
    if not os.path.exists(genome_fasta) and search_if_not_found:
        # Try to find the genome FASTA file
        found_files = find_fastq_files(genome_fasta)  # Reuse the search function
        if not found_files:
            raise RuntimeError(f"Could not find genome FASTA file: {genome_fasta}")
        genome_fasta = found_files[0]
    
    if not os.path.exists(genome_fasta):
        raise RuntimeError(f"Genome FASTA file not found: {genome_fasta}")
    
    # Check GTF file if provided
    if gtf_file and not os.path.exists(gtf_file) and search_if_not_found:
        # Try to find the GTF file
        found_files = find_fastq_files(gtf_file)  # Reuse the search function
        if found_files:
            gtf_file = found_files[0]
    
    if gtf_file and not os.path.exists(gtf_file):
        raise RuntimeError(f"GTF file not found: {gtf_file}")
    
    # Create genome directory if it doesn't exist
    if not os.path.exists(genome_dir):
        os.makedirs(genome_dir)
    
    # Build STAR command
    cmd = [
        star_path,
        "--runThreadN", str(threads),
        "--runMode", "genomeGenerate",
        "--genomeDir", genome_dir,
        "--genomeFastaFiles", genome_fasta,
        "--sjdbOverhang", str(sjdb_overhang)
    ]
    
    # Add GTF file if provided
    if gtf_file:
        cmd.extend(["--sjdbGTFfile", gtf_file])
    
    # Run STAR genome generation
    print(f"Generating STAR genome index in {genome_dir}...")
    print(f"Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        error_msg = result.stderr if result.stderr else "Unknown error"
        raise RuntimeError(f"STAR genome index generation failed: {error_msg}")
    
    # Check if index files were created
    expected_files = ["Genome", "SA", "SAindex"]
    missing_files = []
    for file in expected_files:
        if not os.path.exists(os.path.join(genome_dir, file)):
            missing_files.append(file)
    
    if missing_files:
        raise RuntimeError(f"STAR genome index generation completed but missing files: {missing_files}")
    
    print(f"STAR genome index successfully generated in {genome_dir}")
    return genome_dir

def generate_star_genome_index_background(genome_dir: str, genome_fasta: str, gtf_file: str = None,
                                        sjdb_overhang: int = 99, threads: int = 8, 
                                        job_id: Optional[str] = None, search_if_not_found: bool = True) -> Dict:
    """Generate a STAR genome index in the background.
    
    Args:
        genome_dir: Directory to store the genome index
        genome_fasta: Path to the genome FASTA file
        gtf_file: Optional path to GTF annotation file
        sjdb_overhang: Overhang for splice junction database (default: 99 for 100bp reads)
        threads: Number of threads to use for index generation
        job_id: Optional custom job ID. If not provided, will be auto-generated
        search_if_not_found: If True, search for files if full path doesn't exist
        
    Returns:
        Dictionary containing job_id, status, and other job information
    """
    global _star_processes
    
    # Generate job ID if not provided
    if job_id is None:
        base_name = os.path.splitext(os.path.basename(genome_fasta))[0]
        job_id = f"star_index_{base_name}_{int(time.time())}"
    
    # Check if job_id already exists
    if job_id in _star_processes:
        raise RuntimeError(f"Job ID '{job_id}' already exists. Please use a different job ID.")
    
    # Check if STAR is available
    star_path = shutil.which("STAR")
    if not star_path:
        # Try common install locations
        for path in ["/usr/local/bin/STAR", "/opt/anaconda3/bin/STAR"]:
            if os.path.exists(path):
                star_path = path
                break
        if not star_path:
            raise RuntimeError("STAR not found. Please install STAR or run install_star().")
    
    if not os.path.exists(star_path):
        raise RuntimeError(f"STAR not found at {star_path}. Please check your installation.")
    
    # Validate input files
    if not os.path.exists(genome_fasta) and search_if_not_found:
        # Try to find the genome FASTA file
        found_files = find_fastq_files(genome_fasta)  # Reuse the search function
        if not found_files:
            raise RuntimeError(f"Could not find genome FASTA file: {genome_fasta}")
        genome_fasta = found_files[0]
    
    if not os.path.exists(genome_fasta):
        raise RuntimeError(f"Genome FASTA file not found: {genome_fasta}")
    
    # Check GTF file if provided
    if gtf_file and not os.path.exists(gtf_file) and search_if_not_found:
        # Try to find the GTF file
        found_files = find_fastq_files(gtf_file)  # Reuse the search function
        if found_files:
            gtf_file = found_files[0]
    
    if gtf_file and not os.path.exists(gtf_file):
        raise RuntimeError(f"GTF file not found: {gtf_file}")
    
    # Create genome directory if it doesn't exist
    if not os.path.exists(genome_dir):
        os.makedirs(genome_dir)
    
    # Build STAR command
    cmd = [
        star_path,
        "--runThreadN", str(threads),
        "--runMode", "genomeGenerate",
        "--genomeDir", genome_dir,
        "--genomeFastaFiles", genome_fasta,
        "--sjdbOverhang", str(sjdb_overhang)
    ]
    
    # Add GTF file if provided
    if gtf_file:
        cmd.extend(["--sjdbGTFfile", gtf_file])
    
    # Initialize job info
    job_info = {
        "job_id": job_id,
        "genome_dir": genome_dir,
        "genome_fasta": genome_fasta,
        "gtf_file": gtf_file,
        "sjdb_overhang": sjdb_overhang,
        "threads": threads,
        "command": " ".join(cmd),
        "status": "starting",
        "start_time": time.time(),
        "end_time": None,
        "process": None,
        "stdout": "",
        "stderr": "",
        "return_code": None,
        "error": None
    }
    
    def run_genome_generation():
        """Background function to run STAR genome generation"""
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
            _star_process_objects[job_id] = process
            
            # Wait for completion
            stdout, stderr = process.communicate()
            job_info["stdout"] = stdout
            job_info["stderr"] = stderr
            job_info["return_code"] = process.returncode
            job_info["end_time"] = time.time()
            
            # Check if index files were created
            expected_files = ["Genome", "SA", "SAindex"]
            missing_files = []
            for file in expected_files:
                if not os.path.exists(os.path.join(genome_dir, file)):
                    missing_files.append(file)
            
            if process.returncode == 0 and not missing_files:
                job_info["status"] = "completed"
            else:
                job_info["status"] = "failed"
                if missing_files:
                    job_info["error"] = f"Missing index files: {missing_files}"
                else:
                    job_info["error"] = stderr if stderr else "Unknown error"
                
        except Exception as e:
            job_info["status"] = "failed"
            job_info["error"] = str(e)
            job_info["end_time"] = time.time()
        finally:
            # Clean up process object reference
            if job_id in _star_process_objects:
                del _star_process_objects[job_id]
    
    # Start the background thread
    thread = threading.Thread(target=run_genome_generation)
    thread.daemon = True
    thread.start()
    
    # Store job info
    _star_processes[job_id] = job_info
    
    return {
        "job_id": job_id,
        "status": "started",
        "message": f"STAR genome index generation job '{job_id}' started in background"
    } 

def check_system_requirements() -> dict:
    """Check system requirements for STAR installation and compilation.
    Returns:
        Dictionary containing status of all required components
    """
    result = {
        "system": platform.system(),
        "architecture": platform.machine(),
        "gcc_installed": False,
        "gcc_path": None,
        "gcc_version": None,
        "clang_installed": False,
        "clang_path": None,
        "clang_version": None,
        "libomp_installed": False,
        "libomp_path": None,
        "brew_installed": False,
        "make_installed": False,
        "make_path": None,
        "wget_installed": False,
        "wget_path": None,
        "tar_installed": False,
        "tar_path": None,
        "star_installed": False,
        "star_path": None,
        "star_version": None,
        "recommendations": [],
        "can_install_star": True,
        "installation_ready": True
    }
    
    try:
        # Check GCC
        gcc_path = shutil.which("g++")
        if gcc_path:
            result["gcc_installed"] = True
            result["gcc_path"] = gcc_path
            try:
                proc = subprocess.run([gcc_path, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                result["gcc_version"] = proc.stdout.strip().split('\n')[0]
            except:
                result["gcc_version"] = "Version check failed"
        else:
            result["recommendations"].append("Install GCC for C++ compilation")
        
        # Check Clang (important for macOS)
        clang_path = shutil.which("clang++")
        if clang_path:
            result["clang_installed"] = True
            result["clang_path"] = clang_path
            try:
                proc = subprocess.run([clang_path, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                result["clang_version"] = proc.stdout.strip().split('\n')[0]
            except:
                result["clang_version"] = "Version check failed"
        else:
            result["recommendations"].append("Install Clang for C++ compilation (especially on macOS)")
        
        # Check Homebrew (for macOS)
        brew_path = shutil.which("brew")
        if brew_path:
            result["brew_installed"] = True
        else:
            if platform.system() == "Darwin":
                result["recommendations"].append("Install Homebrew for package management on macOS")
        
        # Check libomp (OpenMP library for macOS)
        if platform.system() == "Darwin" and result["brew_installed"]:
            try:
                proc = subprocess.run(["brew", "list", "libomp"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if proc.returncode == 0:
                    result["libomp_installed"] = True
                    result["libomp_path"] = "Installed via Homebrew"
                else:
                    result["recommendations"].append("Install libomp: brew install libomp")
            except:
                result["recommendations"].append("Install libomp: brew install libomp")
        
        # Check make
        make_path = shutil.which("make")
        if make_path:
            result["make_installed"] = True
            result["make_path"] = make_path
        else:
            result["recommendations"].append("Install make for building software")
        
        # Check wget
        wget_path = shutil.which("wget")
        if wget_path:
            result["wget_installed"] = True
            result["wget_path"] = wget_path
        else:
            result["recommendations"].append("Install wget for downloading files")
        
        # Check tar
        tar_path = shutil.which("tar")
        if tar_path:
            result["tar_installed"] = True
            result["tar_path"] = tar_path
        else:
            result["recommendations"].append("Install tar for extracting archives")
        
        # Check STAR
        star_path = shutil.which("STAR")
        if star_path:
            result["star_installed"] = True
            result["star_path"] = star_path
            try:
                proc = subprocess.run([star_path, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                result["star_version"] = proc.stdout.strip() or proc.stderr.strip()
            except:
                result["star_version"] = "Version check failed"
        
        # Add system-specific recommendations
        if platform.system() == "Darwin":
            if not result["libomp_installed"]:
                result["recommendations"].append("On macOS, libomp is required for OpenMP support")
                result["installation_ready"] = False
            if not result["clang_installed"]:
                result["recommendations"].append("On macOS, Clang is preferred over GCC for compilation")
        
        # Check if all required tools are available
        required_tools = ["make", "wget", "tar"]
        missing_tools = []
        for tool in required_tools:
            if not result.get(f"{tool}_installed", False):
                missing_tools.append(tool)
        
        if missing_tools:
            result["recommendations"].append(f"Install missing tools: {', '.join(missing_tools)}")
            result["installation_ready"] = False
        
        # Check if we have a suitable compiler
        if not result["clang_installed"] and not result["gcc_installed"]:
            result["recommendations"].append("Install a C++ compiler (Clang or GCC)")
            result["installation_ready"] = False
        
        # Check if STAR is already installed
        if result["star_installed"]:
            result["can_install_star"] = False
            result["recommendations"].append("STAR is already installed")
        
    except Exception as e:
        result["error"] = str(e)
        result["can_install_star"] = False
        result["installation_ready"] = False
    
    return result 