import os
import glob
import shutil
import subprocess
import platform

def find_fastq_files(filename: str = None, search_dir: str = None) -> list:
    """Search for FASTQ files by name or pattern. Returns a list of found files with full paths."""
    if search_dir is None:
        # Default search directories
        search_dirs = [
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents"),
            os.getcwd()  # Current working directory
        ]
    else:
        search_dirs = [search_dir]
    found_files = []
    for directory in search_dirs:
        if not os.path.exists(directory):
            continue
        if filename:
            # Search for specific filename
            patterns = [
                os.path.join(directory, filename),
                os.path.join(directory, f"*{filename}*"),
                os.path.join(directory, f"*{filename}*.fastq"),
                os.path.join(directory, f"*{filename}*.fq"),
                os.path.join(directory, f"*{filename}*.fastq.gz"),
                os.path.join(directory, f"*{filename}*.fq.gz")
            ]
        else:
            # Search for all FASTQ files
            patterns = [
                os.path.join(directory, "*.fastq"),
                os.path.join(directory, "*.fq"),
                os.path.join(directory, "*.fastq.gz"),
                os.path.join(directory, "*.fq.gz")
            ]
        for pattern in patterns:
            found_files.extend(glob.glob(pattern))
    # Remove duplicates and sort
    found_files = sorted(list(set(found_files)))
    return found_files

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