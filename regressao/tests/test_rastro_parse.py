"""regressao/rastro/parse.py: parse de arquivos .php com nikic/php-parser dentro do contêiner (docker simulado)."""
from regressao.rastro import parse


def test_parse_arquivo_valido_e_invalido(monkeypatch):
    chamadas = []

    def falso_docker(args, timeout, stdin=None, stdout=None):
        chamadas.append(args)
        if args[0] == "cp":
            return b""
        return (b"OK\tbom.php\n"
                b"FALHA\truim.php\tSyntax error, unexpected T_STRING on line 3\n")

    monkeypatch.setattr(parse, "_docker", falso_docker)
    r = parse.roda_parse(["bom.php", "ruim.php"])
    assert r["ok"] == 1
    assert r["falhas"] == [{"arquivo": "ruim.php", "msg": "Syntax error, unexpected T_STRING on line 3"}]
    assert any(a[0] == "cp" for a in chamadas)  # o script PHP e copiado para o contêiner antes de rodar
    assert chamadas[-1][0] == "exec" and "-i" in chamadas[-1]  # e a lista segue por stdin ao ultimo exec


def test_lista_vazia_nao_chama_o_docker(monkeypatch):
    monkeypatch.setattr(parse, "_docker", lambda *a, **k: (_ for _ in ()).throw(AssertionError("nao deveria chamar")))
    assert parse.roda_parse([]) == {"ok": 0, "falhas": []}
