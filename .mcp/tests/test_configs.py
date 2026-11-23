"""Os arquivos de configuracao das IAs (Cursor, VS Code, Claude Code) apontam para um servidor que sobe de verdade."""
import json
from pathlib import Path

import anyio
import pytest
from mcp import Client, StdioServerParameters

RAIZ = Path(__file__).resolve().parents[2]
CONFIGS = {
    ".cursor/mcp.json": "mcpServers",
    ".vscode/mcp.json": "servers",
    ".mcp.json": "mcpServers",
}


def _expande(valor: str) -> str:
    valor = valor.replace("${workspaceFolder}", str(RAIZ))
    return valor if valor.startswith("/") else str(RAIZ / valor)


@pytest.mark.parametrize("arquivo,chave", CONFIGS.items())
def test_config_valida_e_sobe(arquivo, chave):
    cfg = json.loads((RAIZ / arquivo).read_text())
    srv = cfg[chave]["ecidade"]
    assert srv.get("type", "stdio") == "stdio"
    comando = _expande(srv["command"])
    args = [_expande(a) for a in srv["args"]]
    assert comando.endswith(".mcp/.venv/bin/python") and args == [str(RAIZ / ".mcp/servidor/main.py")]

    async def go():
        # cwd = raiz: e como Claude Code/Cursor/VS Code abrem o projeto
        async with Client(StdioServerParameters(command=comando, args=args, cwd=str(RAIZ))) as c:
            return c.server_info.name, len((await c.list_tools()).tools)
    nome, n = anyio.run(go)
    assert nome == "ecidade-migracao" and n == 13
