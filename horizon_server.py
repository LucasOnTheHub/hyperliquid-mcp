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
# rien que pour démarrer (dérivation de l'adresse du wallet). Sans clé exploitable,
# l'inspection échoue et le build casse.
#
# Attention : le conteneur de build DÉFINIT bien HYPERLIQUID_PRIVATE_KEY (via un
# `ENV` du Dockerfile généré), mais avec une valeur de remplacement — les vrais
# secrets ne sont pas gravés dans une couche d'image. Tester la seule présence de
# la variable ne suffit donc pas : il faut valider sa valeur.


def _cle_exploitable(valeur):
    """Vrai si la valeur est une clé privée secp256k1 utilisable (32 octets hex)."""
    if not valeur:
        return False
    brut = valeur[2:] if valeur[:2].lower() == "0x" else valeur
    if len(brut) != 64:
        return False
    try:
        bytes.fromhex(brut)
    except ValueError:
        return False
    return True


# Clé factice sans fonds, uniquement pour que le build puisse lister les outils.
# Dès qu'Horizon injecte une vraie clé au runtime, elle est jugée exploitable et
# conservée telle quelle : ce bloc devient alors sans effet.
if not _cle_exploitable(env.get("HYPERLIQUID_PRIVATE_KEY")):
    env["HYPERLIQUID_PRIVATE_KEY"] = "0x" + "11" * 32
    # Pas de vraie clé = on n'est pas en production : on force le testnet pour
    # qu'aucune requête ne parte vers le mainnet pendant l'inspection. On écrase
    # ici au lieu d'un setdefault, car la variable peut elle aussi porter une
    # valeur de remplacement au build.
    env["HYPERLIQUID_TESTNET"] = "true"

# Garde-fou indépendant du build : en l'absence de consigne explicite, on reste
# sur le testnet plutôt que d'envoyer des ordres réels sur le mainnet.
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
