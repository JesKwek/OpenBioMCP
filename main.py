# server.py
from mcp.server.fastmcp import FastMCP
from modules.fastqc import register_fastqc_tools

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

if __name__ == "__main__":
    mcp.run()