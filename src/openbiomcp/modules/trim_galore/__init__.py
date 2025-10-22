from .trim_galore import (
    trim_galore,
    install_trim_galore,
    is_trim_galore_installed,
    trim_galore_background,
    get_trim_galore_status,
    list_trim_galore_jobs,
    stop_trim_galore_job,
    cleanup_trim_galore_jobs
)

def register_trim_galore_tools(mcp):
    mcp.tool()(trim_galore)
    mcp.tool()(install_trim_galore)
    mcp.tool()(is_trim_galore_installed)
    mcp.tool()(trim_galore_background)
    mcp.tool()(get_trim_galore_status)
    mcp.tool()(list_trim_galore_jobs)
    mcp.tool()(stop_trim_galore_job)
    mcp.tool()(cleanup_trim_galore_jobs) 