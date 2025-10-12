from .star_alignment import (
    run_star_alignment,
    star_alignment_background,
    get_star_status,
    list_star_jobs,
    stop_star_job,
    cleanup_star_jobs,
    install_star,
    uninstall_star,
    is_star_installed,
    generate_star_genome_index,
    generate_star_genome_index_background,
    check_system_requirements,
    get_macos_manual_installation_guide,
)

def register_star_alignment_tools(mcp):
    """Register all STAR alignment tools with the MCP server."""
    mcp.tool()(run_star_alignment)
    mcp.tool()(star_alignment_background)
    mcp.tool()(get_star_status)
    mcp.tool()(list_star_jobs)
    mcp.tool()(stop_star_job)
    mcp.tool()(cleanup_star_jobs)
    mcp.tool()(install_star)
    mcp.tool()(uninstall_star)
    mcp.tool()(is_star_installed)
    mcp.tool()(generate_star_genome_index)
    mcp.tool()(generate_star_genome_index_background)
    mcp.tool()(check_system_requirements)
    mcp.tool()(get_macos_manual_installation_guide) 