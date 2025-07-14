from .fastqc import (
    find_fastq_files,
    fastqc,
    install_fastqc,
    is_fastqc_installed,
)

def register_fastqc_tools(mcp):
    mcp.tool()(find_fastq_files)
    mcp.tool()(fastqc)
    mcp.tool()(install_fastqc)
    mcp.tool()(is_fastqc_installed) 