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

# Pendant le build, Horizon exécute `fastmcp inspect` pour lister les outils AVANT
# que les vraies variables d'environnement (définies dans l'UI Horizon) ne soient
# injectées dans le conteneur. Le serveur Hyperliquid exige une clé privée valide
# rien que pour démarrer (dérivation de l'adresse du wallet). Sans clé, l'inspection
# échoue et le build casse.
# On fournit donc une clé factice UNIQUEMENT si HYPERLIQUID_PRIVATE_KEY est absente,
# juste pour permettre au build de lister les outils. Elle n'a aucun fonds et ne sert
# à rien en production : une fois déployé, Horizon injecte la vraie clé configurée
# dans l'UI, qui prend le dessus ici via env.setdefault.
env.setdefault("HYPERLIQUID_PRIVATE_KEY", "0x" + "11" * 32)
env.setdefault("HYPERLIQUID_TESTNET", "true")

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
