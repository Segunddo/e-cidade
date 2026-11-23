"""Servidor de verdade, em subprocesso, falando stdio: cliente oficial e JSON-RPC cru (stdout so protocolo)."""
import json
import os
import queue
import subprocess
import sys
import threading
from pathlib import Path

import anyio
import pytest
from mcp import Client, StdioServerParameters

MAIN = Path(__file__).resolve().parents[1] / "servidor" / "main.py"
MCP_DIR = MAIN.parents[1]


@pytest.fixture
def env(raiz, tmp_path):
    docker = tmp_path / "docker_falso"
    # escreve no stdout e no stderr e falha: nada disso pode vazar para o protocolo
    docker.write_text("#!/bin/sh\necho 'lixo no stdout do docker'\necho 'Error: No such object' >&2\nexit 1\n")
    docker.chmod(0o755)
    (raiz / ".mcp" / "docs" / "regras-arquitetura.md").write_text("# Regras\n")
    return {"PATH": os.environ["PATH"], "HOME": str(tmp_path), "ECIDADE_MCP_RAIZ": str(raiz),
            "ECIDADE_MCP_DOCKER": str(docker), "ECIDADE_MCP_USUARIO": "stdio-tester"}


def test_cliente_oficial_por_stdio(env):
    async def go():
        params = StdioServerParameters(command=sys.executable, args=[str(MAIN)], env=env, cwd=str(MCP_DIR.parent))
        async with Client(params) as c:
            tools = (await c.list_tools()).tools
            r = await c.call_tool("buscar_codigo_legado", {"padrao": "parse_str_1_arg"})
            v = await c.call_tool("validar_arquivo_php", {"caminho": "ecidade/tela001.php"})
            res = (await c.list_resources()).resources
            pr = (await c.list_prompts()).prompts
            return tools, r, v, res, pr
    tools, r, v, res, pr = anyio.run(go)
    assert len(tools) == 13
    assert r.structured_content["dados"]["ocorrencias"][0]["linha"] == 2
    assert v.structured_content["dados"]["resultados"][0]["erro"]["codigo"] == "conteiner_indisponivel"
    assert len(res) == 9 and len(pr) == 4


class Sessao:
    """JSON-RPC cru sobre o stdin/stdout do processo; guarda TODAS as linhas de stdout."""

    def __init__(self, argv, env, cwd):
        self.p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  env=env, cwd=cwd)
        self.linhas: list[bytes] = []
        self.fila: queue.Queue = queue.Queue()
        self.stderr = b""
        self._leitores = [threading.Thread(target=self._le, daemon=True),
                          threading.Thread(target=self._le_err, daemon=True)]
        for t in self._leitores:
            t.start()

    def _le(self):
        for linha in self.p.stdout:
            self.linhas.append(linha)
            self.fila.put(linha)

    def _le_err(self):
        self.stderr = self.p.stderr.read()

    def envia(self, msg):
        self.p.stdin.write((json.dumps(msg) + "\n").encode())
        self.p.stdin.flush()

    def pede(self, id_, metodo, params=None):
        self.envia({"jsonrpc": "2.0", "id": id_, "method": metodo, "params": params or {}})
        while True:
            m = json.loads(self.fila.get(timeout=60))
            if m.get("id") == id_:
                return m

    def fecha(self):
        self.p.stdin.close()
        self.p.wait(timeout=30)
        for t in self._leitores:  # sem o join, linhas/stderr podiam ser conferidos antes de lidos por inteiro
            t.join(timeout=30)


def _sessao_completa(s: Sessao):
    init = s.pede(1, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                    "clientInfo": {"name": "teste-cru", "version": "0"}})
    assert init["result"]["serverInfo"]["name"] == "ecidade-migracao"
    s.envia({"jsonrpc": "2.0", "method": "notifications/initialized"})
    assert len(s.pede(2, "tools/list")["result"]["tools"]) >= 13
    r = s.pede(3, "tools/call", {"name": "validar_arquivo_php", "arguments": {"caminho": "ecidade/tela001.php"}})
    assert r["result"]["structuredContent"]["ok"] is True
    r = s.pede(4, "tools/call", {"name": "buscar_codigo_legado", "arguments": {"padrao": "split", "caminho": "../.."}})
    assert r["result"]["structuredContent"]["erro"]["codigo"] == "caminho_fora_da_raiz"
    assert len(s.pede(5, "resources/list")["result"]["resources"]) == 9
    assert len(s.pede(6, "prompts/list")["result"]["prompts"]) == 4
    s.pede(7, "resources/read", {"uri": "ecidade://estado/trabalho"})
    s.pede(8, "tools/call", {"name": "quadro", "arguments": {}})
    s.fecha()


def _so_json_rpc(linhas):
    assert linhas, "nenhuma resposta"
    for linha in linhas:
        m = json.loads(linha)  # explode se houver qualquer texto que nao seja JSON
        assert m.get("jsonrpc") == "2.0", linha


def test_stdout_so_tem_json_rpc(env):
    s = Sessao([sys.executable, str(MAIN)], env, str(MCP_DIR.parent))
    _sessao_completa(s)
    _so_json_rpc(s.linhas)
    assert b"iniciando" in s.stderr  # o log foi para o stderr


def test_print_e_subprocesso_dentro_de_tool_nao_vazam(env, tmp_path):
    """Mesmo uma tool mal comportada (print, os.system) nao corrompe o protocolo."""
    script = tmp_path / "servidor_ruidoso.py"
    script.write_text(
        "import os, subprocess, sys\n"
        f"sys.path.insert(0, {str(MCP_DIR)!r})\n"
        "from servidor.main import criar_servidor, servir\n"
        "mcp = criar_servidor()\n"
        "@mcp.tool(name='barulho')\n"
        "def barulho() -> str:\n"
        "    print('PRINT NO STDOUT')\n"
        "    print('PRINT SEM QUEBRA', end='')\n"
        "    subprocess.run(['echo', 'SUBPROCESSO NO STDOUT'])  # herda o fd 1\n"
        "    os.write(1, b'WRITE NO FD 1\\n')\n"
        "    return 'ok'\n"
        "servir(mcp)\n")
    s = Sessao([sys.executable, str(script)], env, str(tmp_path))
    s.pede(1, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                             "clientInfo": {"name": "teste-cru", "version": "0"}})
    s.envia({"jsonrpc": "2.0", "method": "notifications/initialized"})
    r = s.pede(2, "tools/call", {"name": "barulho", "arguments": {}})
    assert r["result"]["content"][0]["text"] == "ok"
    s.fecha()
    _so_json_rpc(s.linhas)
    for marca in (b"PRINT NO STDOUT", b"PRINT SEM QUEBRA", b"SUBPROCESSO NO STDOUT", b"WRITE NO FD 1"):
        assert marca in s.stderr, marca


def test_ecidade_mcp_log_invalido_nao_derruba_a_inicializacao(env):
    s = Sessao([sys.executable, str(MAIN)], {**env, "ECIDADE_MCP_LOG": "barulhento"}, str(MCP_DIR.parent))
    init = s.pede(1, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                    "clientInfo": {"name": "teste-cru", "version": "0"}})
    s.fecha()
    assert init["result"]["serverInfo"]["name"] == "ecidade-migracao"
    assert b"ECIDADE_MCP_LOG" in s.stderr and b"iniciando" in s.stderr


def test_import_nao_escreve_no_stdout():
    r = subprocess.run([sys.executable, "-c", "import servidor.main"], cwd=str(MCP_DIR), capture_output=True,
                       timeout=60)
    assert r.returncode == 0 and r.stdout == b""
