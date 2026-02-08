"""PIISCAN MCP server — exposes scan() as an MCP tool for Cognis.Studio."""
from __future__ import annotations
from piiscan.core import scan, to_json

def serve() -> int:
    """Start an MCP stdio server. Requires the optional 'mcp' extra:
        pip install "cognis-piiscan[mcp]"
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception:
        print("Install the MCP extra: pip install 'cognis-piiscan[mcp]'")
        return 1
    app = FastMCP("piiscan")

    @app.tool()
    def piiscan_scan(target: str) -> str:
        """PII discovery across warehouses and lakes (data-side scanner). Returns JSON findings."""
        return to_json(scan(target))

    app.run()
    return 0
