from .fastqc import (
    find_fastq_files,
    fastqc,
    fastqc_background,
    get_fastqc_status,
    list_fastqc_jobs,
    stop_fastqc_job,
    cleanup_fastqc_jobs,
    install_fastqc,
    is_fastqc_installed,
)

def register_fastqc_tools(mcp):
    mcp.tool()(find_fastq_files)
    mcp.tool()(fastqc)
    mcp.tool()(fastqc_background)
    mcp.tool()(get_fastqc_status)
    mcp.tool()(list_fastqc_jobs)
    mcp.tool()(stop_fastqc_job)
    mcp.tool()(cleanup_fastqc_jobs)
    mcp.tool()(install_fastqc)
    mcp.tool()(is_fastqc_installed) 