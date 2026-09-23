"""Entrypoint pour Prefect Horizon : expose le serveur stdio existant via un proxy FastMCP."""
import os
import sys
from pathlib import Path

from fastmcp import FastMCP

ROOT = Path(__file__).parent

# Le sous-processus stdio ne reçoit pas l'env du parent par défaut : on le transmet
# (HYPERLIQUID_* définis dans Horizon, PATH, certificats, etc.).
env = dict(os.environ)
env["PYTHONPATH"] = str(ROOT / "src")

mcp = FastMCP.as_proxy(
    {
        "mcpServers": {
            "hyperliquid": {
                "command": sys.executable,
                "args": ["-m", "hyperliquid_mcp.server"],
                "env": env,
                "cwd": str(ROOT),
            }
        }
    },
    name="hyperliquid",
)

if __name__ == "__main__":
    mcp.run()
