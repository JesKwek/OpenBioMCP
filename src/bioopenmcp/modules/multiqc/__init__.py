from .multiqc import (
    multiqc,
    multiqc_background,
    get_multiqc_status,
    list_multiqc_jobs,
    stop_multiqc_job,
    cleanup_multiqc_jobs,
    install_multiqc,
    is_multiqc_installed,
    fix_multiqc_path,
)

def register_multiqc_tools(mcp):
    mcp.tool()(multiqc)
    mcp.tool()(multiqc_background)
    mcp.tool()(get_multiqc_status)
    mcp.tool()(list_multiqc_jobs)
    mcp.tool()(stop_multiqc_job)
    mcp.tool()(cleanup_multiqc_jobs)
    mcp.tool()(install_multiqc)
    mcp.tool()(is_multiqc_installed)
    mcp.tool()(fix_multiqc_path)
