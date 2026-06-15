"""PIISCAN MCP server — exposes scan() as an MCP tool for Cognis.Studio."""
from __future__ import annotations

import json

from piiscan.core import load_csv, scan_dataset


def serve() -> int:
    """Start an MCP stdio server. Requires the optional 'mcp' extra:
        pip install "cognis-piiscan[mcp]"
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print("Install the MCP extra: pip install 'cognis-piiscan[mcp]'")
        return 1

    app = FastMCP("piiscan")

    @app.tool()
    def piiscan_scan(path: str, sample: int = 1000) -> str:
        """Scan a CSV file for PII. Returns JSON findings.

        Parameters
        ----------
        path:   Absolute path to a CSV file.
        sample: Max rows to sample per column (default 1000).
        """
        try:
            dataset_name, columns = load_csv(path, sample=sample)
        except FileNotFoundError:
            return json.dumps({"error": f"file not found: {path}"})
        except (ValueError, OSError, UnicodeDecodeError) as exc:
            return json.dumps({"error": str(exc)})
        report = scan_dataset(dataset_name, columns)
        return json.dumps(report.to_dict(), indent=2)

    app.run()
    return 0
