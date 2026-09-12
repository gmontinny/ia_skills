"""
Entrypoint stdio para clientes MCP que iniciam o servidor como processo local.
Usado pelo Antigravity Desktop e outros clientes que usam command/args.
"""
import sys
import os

# Garante que o diretório do projeto está no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.mcp_server import mcp

if __name__ == "__main__":
    mcp.run(transport="stdio")
