from .cutadapt import (
    is_cutadapt_installed,
    install_cutadapt,
    run_cutadapt,
    cutadapt_background,
    get_cutadapt_status,
    list_cutadapt_jobs,
    stop_cutadapt_job,
    cleanup_cutadapt_jobs
)

def register_cutadapt_tools(mcp):
    mcp.tool()(is_cutadapt_installed)
    mcp.tool()(install_cutadapt)
    mcp.tool()(run_cutadapt)
    mcp.tool()(cutadapt_background)
    mcp.tool()(get_cutadapt_status)
    mcp.tool()(list_cutadapt_jobs)
    mcp.tool()(stop_cutadapt_job)
    mcp.tool()(cleanup_cutadapt_jobs) 