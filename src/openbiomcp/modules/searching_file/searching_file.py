import os
import glob

def find_fastq_files(filename: str = None, search_dir: str = None) -> list:
    """Search for FASTQ files by name or pattern. Returns a list of found files with full paths."""
    if search_dir is None:
        search_dirs = [
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents"),
            os.getcwd()
        ]
    else:
        search_dirs = [search_dir]
    found_files = []
    for directory in search_dirs:
        if not os.path.exists(directory):
            continue
        if filename:
            patterns = [
                os.path.join(directory, filename),
                os.path.join(directory, f"*{filename}*"),
                os.path.join(directory, f"*{filename}*.fastq"),
                os.path.join(directory, f"*{filename}*.fq"),
                os.path.join(directory, f"*{filename}*.fastq.gz"),
                os.path.join(directory, f"*{filename}*.fq.gz")
            ]
        else:
            patterns = [
                os.path.join(directory, "*.fastq"),
                os.path.join(directory, "*.fq"),
                os.path.join(directory, "*.fastq.gz"),
                os.path.join(directory, "*.fq.gz")
            ]
        for pattern in patterns:
            found_files.extend(glob.glob(pattern))
    found_files = sorted(list(set(found_files)))
    return found_files 