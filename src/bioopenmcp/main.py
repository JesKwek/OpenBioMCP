# server.py
from mcp.server.fastmcp import FastMCP
from bioopenmcp.modules.fastqc import register_fastqc_tools
from bioopenmcp.modules.cutadapt import register_cutadapt_tools
from bioopenmcp.modules.trim_galore import register_trim_galore_tools
from bioopenmcp.modules.star_alignment import register_star_alignment_tools
from bioopenmcp.modules.multiqc import register_multiqc_tools

import subprocess
import shutil
import os

# Create an MCP server
mcp = FastMCP("BioOpenMCP")

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}! This is an BioOpenMCP server."

# Register all FastQC tools
register_fastqc_tools(mcp)

# Register all cutadapt tools
register_cutadapt_tools(mcp)

# Register all trim_galore tools
register_trim_galore_tools(mcp)

# Register all STAR alignment tools
register_star_alignment_tools(mcp)

# Register all MultiQC tools
register_multiqc_tools(mcp)

def main():
    mcp.run()

if __name__ == "__main__":
    main()