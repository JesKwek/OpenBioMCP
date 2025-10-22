# server.py
from mcp.server.fastmcp import FastMCP
from openbiomcp.modules.fastqc import register_fastqc_tools
from openbiomcp.modules.cutadapt import register_cutadapt_tools
from openbiomcp.modules.trim_galore import register_trim_galore_tools
from openbiomcp.modules.star_alignment import register_star_alignment_tools
from openbiomcp.modules.multiqc import register_multiqc_tools

import subprocess
import shutil
import os

# Create an MCP server
mcp = FastMCP("OpenBioMCP")

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}! This is an OpenBioMCP server."

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