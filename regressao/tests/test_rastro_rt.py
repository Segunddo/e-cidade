"""regressao/rastro/php/rt.php: eventos gravados pelas sondas, nos dois PHP (contêineres reais)."""
import json

import pytest

from regressao.nucleo.ambiente import containers_do_ambiente
from regressao.nucleo.banco import _docker
from regressao.tests.test_rastro_instrumentador import PHP_DIR, _envia

B = "/tmp/rastro_rt"
RT = (PHP_DIR / "rt.php").read_bytes()


def _roda(container: str, nome: str, codigo: str, **env: str) -> tuple[str, list[dict]]:
    _envia(container, f"{B}/{nome}", {"s.php": codigo.encode()})
    ids = f"{nome}_{container[-2:]}"
    e = " ".join(f"{k}={v}" for k, v in {"RASTRO_ID": ids, "RASTRO_PREFIXOS": f"{B}/{nome}/", **env}.items())
    saida = _docker(["exec", container, "sh", "-c",
                     f"cd {B}/{nome} && {e} php -d display_errors=0 -d auto_prepend_file={B}/rt/rt.php s.php 2>&1; true"],
                    60).decode("latin-1")
    bruto = _docker(["exec", container, "sh", "-c", f"cat /tmp/rastro/{ids}.jsonl 2>/dev/null; true"], 30).decode()
    return saida, [json.loads(l) for l in bruto.splitlines() if l.strip()]


@pytest.fixture(scope="module")
def cs():
    c = containers_do_ambiente()
    try:
        for n in (c.ref, c.php_novo):
            _docker(["exec", n, "true"], 15)
    except Exception:
        pytest.skip("contêineres docker indisponiveis")
    for n in (c.ref, c.php_novo):
        _envia(n, f"{B}/rt", {"rt.php": RT})
        _docker(["exec", "-u", "root", n, "sh", "-c", "mkdir -p /tmp/rastro && chmod 777 /tmp/rastro"], 15)
    return (c.ref, c.php_novo)


@pytest.mark.parametrize("i", [0, 1])
def test_evento_de_atribuicao_tem_tipo_repr_e_hash(cs, i):
    _, ev = _roda(cs[i], "atrib", '<?php\n$x = 42; __rt_a(1, "x", $x);\n$a = array(1, "b" => 2); __rt_a(2, "a", $a);\n')
    e1, e2 = ev[0], ev[1]
    assert (e1["k"], e1["p"], e1["n"], e1["f"], e1["l"]) == ("a", 1, "x", "s.php", 2)
    assert e1["v"]["t"] == "int" and e1["v"]["r"] == "42" and len(e1["v"]["h"]) == 32
    assert e2["v"]["t"] == "array" and e2["v"]["n"] == 2


@pytest.mark.parametrize("i", [0, 1])
def test_objeto_com_as_mesmas_propriedades_em_outra_ordem_tem_o_mesmo_resumo(cs, i):
    """Propriedades de objeto saem em ordem diferente no 7.4 e no 8.x: o resumo ordena por nome."""
    codigo = ('<?php\n$a = new stdClass; $a->b = 1; $a->a = 2; __rt_a(1, "a", $a);\n'
              '$b = new stdClass; $b->a = 2; $b->b = 1; __rt_a(2, "b", $b);\n')
    _, ev = _roda(cs[i], "objord", codigo)
    assert ev[0]["v"]["h"] == ev[1]["v"]["h"] and ev[0]["v"]["r"] == ev[1]["v"]["r"]


@pytest.mark.parametrize("i", [0, 1])
def test_resource_nao_vaza_o_numero(cs, i):
    _, ev = _roda(cs[i], "res", '<?php\n$r = fopen("php://memory", "r"); __rt_a(1, "r", $r);\n')
    assert ev[0]["v"]["t"] == "resource:stream"
    assert "id #" not in ev[0]["v"]["r"].lower() and not any(ch.isdigit() for ch in ev[0]["v"]["r"])


@pytest.mark.parametrize("i", [0, 1])
def test_aviso_do_php_vira_evento_w_com_arquivo_e_linha(cs, i):
    _, ev = _roda(cs[i], "aviso", '<?php\n__rt_a(1, "x", 1);\ntrigger_error("oi", E_USER_WARNING);\n')
    w = [e for e in ev if e["k"] == "w"]
    assert len(w) == 1 and w[0]["n"] == "user_warning" and w[0]["v"]["r"] == "oi"
    assert (w[0]["f"], w[0]["l"]) == ("s.php", 3)


@pytest.mark.parametrize("i", [0, 1])
def test_handler_anterior_continua_sendo_chamado(cs, i):
    codigo = ('<?php\n__rt_a(1, "x", 1);\n'
              'set_error_handler(function ($n, $m) { echo "app-handler:$m;"; return true; });\n'   # a aplicacao troca o handler
              '__rt_a(2, "y", 2);\ntrigger_error("a", E_USER_WARNING);\n')
    saida, ev = _roda(cs[i], "chain", codigo)
    assert "app-handler:a;" in saida
    assert any(e["k"] == "w" and e["v"]["r"] == "a" for e in ev)


@pytest.mark.parametrize("i", [0, 1])
def test_handler_anterior_recebe_os_mesmos_argumentos_que_receberia_sem_o_rt(cs, i):
    """O 7.4 entrega 5 argumentos ($errcontext) ao handler, o 8.x entrega 4. O rt tem que repassar IGUAL: o handler
    do e-Cidade (Error::_handle) exige 5 e quebraria com ArgumentCountError se recebesse 4 no 7.4."""
    handler = '<?php\nset_error_handler(function () { echo "n=" . func_num_args() . ";"; return true; });\n'
    com_rt = handler + '__rt_a(2, "y", 2);\ntrigger_error("a", E_USER_WARNING);\n'
    sem_rt = handler + 'trigger_error("a", E_USER_WARNING);\n'
    saida_rt, _ = _roda(cs[i], "args_com", com_rt)
    _envia(cs[i], f"{B}/args_sem", {"s.php": sem_rt.encode()})
    saida_sem = _docker(["exec", cs[i], "sh", "-c", f"cd {B}/args_sem && php s.php 2>&1; true"], 30).decode()
    assert saida_rt == saida_sem and saida_sem.startswith("n=")


@pytest.mark.parametrize("i", [0, 1])
def test_so_repassa_ao_handler_da_aplicacao_os_tipos_da_mascara_dela(cs, i):
    """O handler do e-Cidade e registrado com uma mascara (php.error_reporting) e NAO recebe avisos. O rt, que fica
    na frente, so pode repassar o que a mascara permite; os eventos 'w', porem, registram tudo."""
    codigo = ('<?php\n__rt_a(1, "x", 1);\n'
              'set_error_handler(function ($n, $m) { echo "app:$m;"; return true; }, E_ALL & ~E_USER_WARNING);\n'
              '__rt_a(2, "y", 2);\ntrigger_error("fora", E_USER_WARNING);\ntrigger_error("dentro", E_USER_NOTICE);\n')
    saida, ev = _roda(cs[i], "mascara", codigo, RASTRO_MASCARA=str(32767 & ~E_USER_WARNING))
    assert "app:dentro;" in saida and "app:fora;" not in saida
    assert {e["v"]["r"] for e in ev if e["k"] == "w"} == {"fora", "dentro"}


E_USER_WARNING = 512


@pytest.mark.parametrize("i", [0, 1])
def test_erro_fatal_vira_evento_e_nao_perde_o_rastro_ja_gravado(cs, i):
    _, ev = _roda(cs[i], "fatal", '<?php\n__rt_a(1, "x", 1);\nfuncao_que_nao_existe();\n')
    assert [e["k"] for e in ev] == ["a", "e"]
    assert "funcao_que_nao_existe" in ev[1]["v"]["r"] and ev[1]["l"] == 3


@pytest.mark.parametrize("i", [0, 1])
def test_exit_no_meio_preserva_o_flush(cs, i):
    _, ev = _roda(cs[i], "exit", '<?php\n__rt_a(1, "x", 1);\nexit(0);\n__rt_a(2, "y", 2);\n')
    assert [e["n"] for e in ev] == ["x"]


@pytest.mark.parametrize("i", [0, 1])
def test_teto_gera_marca_de_truncado(cs, i):
    _, ev = _roda(cs[i], "teto", '<?php\nfor ($i = 0; $i < 50; $i++) { __rt_a(1, "i", $i); }\n', RASTRO_TETO="10")
    assert ev[-1]["k"] == "T" and len([e for e in ev if e["k"] == "a"]) == 10


def test_sem_id_nao_grava_nada_e_devolve_os_valores(cs):
    _envia(cs[0], f"{B}/semid", {"s.php": b'<?php\n$r = __rt_c(1, "count", [], 7); echo __rt_t(2, $r), __rt_r(3, "ok");\n'})
    saida = _docker(["exec", cs[0], "sh", "-c",
                     f"cd {B}/semid && php -d auto_prepend_file={B}/rt/rt.php s.php"], 30).decode()
    assert saida == "7ok"


def test_mesmo_script_gera_rastro_igual_em_74_e_85(cs):
    codigo = ('<?php\n$x = 3; __rt_a(1, "x", $x);\n$s = "ação"; __rt_a(2, "s", $s);\n$a = array(1, array("k" => "v")); __rt_a(3, "a", $a);\n'
              '$n = null; __rt_a(4, "n", $n);\n$f = 1.5; __rt_a(5, "f", $f);\nif (__rt_t(6, $x > 1)) { echo ""; }\n'
              '$c = __rt_c(7, "count", [isset($a) ? $a : "__unset__"], count($a));\n')
    _, e74 = _roda(cs[0], "igual", codigo)
    _, e85 = _roda(cs[1], "igual", codigo)
    chave = lambda e: (e["k"], e["p"], e["n"], e["f"], e["l"], e["v"].get("t"), e["v"].get("r"), e["v"].get("h"))
    assert [chave(e) for e in e74] == [chave(e) for e in e85]
    assert len(e74) == 7
