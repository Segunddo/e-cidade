"""regressao/rastro/php/analise.php: candidatos de risco e variaveis lidas por linha (roda no contêiner 8.5)."""
import json

import pytest

from regressao.nucleo.ambiente import containers_do_ambiente
from regressao.nucleo.banco import _docker
from regressao.tests.test_rastro_instrumentador import FIXTURES, PHP_DIR, _envia

B = "/tmp/rastro_estatica"


@pytest.fixture(scope="module")
def roda():
    c = containers_do_ambiente()
    try:
        _docker(["exec", c.php_novo, "true"], 15)
    except Exception:
        pytest.skip("contêineres docker indisponiveis")
    scripts = {p.name: p.read_bytes() for p in PHP_DIR.glob("*.php")}
    _envia(c.php_novo, f"{B}/php", scripts)
    _envia(c.php_novo, f"{B}/in", {"candidatos.php": (FIXTURES / "estatica_candidatos.php").read_bytes(),
                                    "leituras.php": (FIXTURES / "estatica_leituras.php").read_bytes(),
                                    "comparacoes.php": (FIXTURES / "estatica_comparacoes.php").read_bytes()})

    def _roda(modo, arquivo):
        saida = _docker(["exec", c.php_novo, "sh", "-c",
                         f"echo {arquivo} | php {B}/php/analise.php --raiz={B}/in --modo={modo} 2>&1"], 60).decode()
        return [json.loads(l) for l in saida.splitlines() if l.startswith("{")]
    return _roda


def test_candidatos_aponta_so_o_uso_sem_checagem(roda):
    r = roda("candidatos", "candidatos.php")
    achados = sorted((c["linha"], c["funcao"], c["variavel"], c["origem"]) for c in r[0]["candidatos"])
    assert achados == [(5, "pg_num_rows", "rs", 4), (20, "pg_num_rows", "rs", 19), (33, "pg_numrows", "rs", 32), (47, "fputs", "fd", 46),
                       (56, "pg_numrows", "rs", 55), (61, "pg_numrows", "rs", 60)]


def test_arquivo_sem_candidato_nao_gera_saida(roda):
    assert roda("candidatos", "leituras.php") == []


def test_leituras_lista_as_variaveis_lidas_em_cada_linha_e_nao_as_atribuidas(roda):
    r = roda("leituras", "leituras.php")[0]["leituras"]
    assert sorted(r["3"]) == ["a", "b"]  # $x = $a + $b;  -> le a e b, nao x
    assert "x" not in r["3"]
    assert sorted(r["4"]) == ["c", "x"]  # $y = f($x, $c);


def test_desestruturacao_escreve_nao_le(roda):
    r = roda("leituras", "leituras.php")[0]["leituras"]
    assert r["8"] == ["data"]                     # list($ano, $mes) = explode('-', $data): le so $data


def test_chamada_em_varias_linhas_vale_para_todas_as_linhas_dela(roda):
    r = roda("leituras", "leituras.php")[0]["leituras"]
    assert all("sql" in r[str(l)] for l in (5, 6, 7))           # a chamada db_query(...) ocupa as linhas 5 a 7


def _comparacoes(roda):
    r = roda("comparacoes", "comparacoes.php")
    return sorted((c["linha"], c["tipo"]) for c in r[0]["comparacoes"])


def test_comparacao_frouxa_com_texto_nao_numerico_e_apontada(roda):
    # $aut == 't' (2), != 'abc' (3), 't' == $aut (4), $o->campo == 't' (14); caso real: ate1_tarefa004 (0 == 't' mudou no PHP 8)
    achados = _comparacoes(roda)
    assert all((l, "texto") in achados for l in (2, 3, 4, 14))


def test_vazio_e_zero_tem_tipo_proprio(roda):
    achados = _comparacoes(roda)
    assert (5, "vazio") in achados and (6, "zero") in achados


def test_switch_com_case_texto_e_apontado_mas_case_numerico_nao(roda):
    linhas = dict(_comparacoes(roda))
    assert linhas.get(16) == "texto" and linhas.get(18) == "texto"      # case 't' e case 'x'
    assert 17 not in linhas                                              # case '1' e numerico


def test_nao_aponta_o_que_nao_muda_de_comportamento(roda):
    linhas = {l for l, _ in _comparacoes(roda)}
    # n==1 (7), '10' numerico (8), === (9), trim() ja e string (10), $_GET e string (11), concat (12), literal==literal (13), "t$suf" (20)
    assert not linhas & {7, 8, 9, 10, 11, 12, 13, 20}


def test_evidencia_de_inteiro_marca_so_quando_a_variavel_recebeu_numero(roda):
    r = {c['linha']: c['evidencia'] for c in roda('comparacoes', 'comparacoes.php')[0]['comparacoes']}
    assert r[22] == 'inteiro' and r[24] == 'inteiro'      # $k = 0 ... $k == 't'; $c = count(...) ... $c == 'abc'
    assert r[26] == ''                                    # $s = 'texto' nao e numero
    assert r[2] == ''                                     # $aut sem atribuicao conhecida: so entra no nivel geral
    assert r[6] == ''                                     # $n == 0: contra o literal 0 a evidencia de inteiro nao agrava


def test_literal_inteiro_diferente_de_zero_nao_e_evidencia(roda):
    r = {c['linha']: c['evidencia'] for c in roda('comparacoes', 'comparacoes.php')[0]['comparacoes']}
    assert r[28] == ''                                    # $p = 5; $p == 't': 5 == 't' e false no 7.4 e no 8.x


def test_comparacao_ja_protegida_contra_zero_nao_e_apontada(roda):
    todos = roda('comparacoes', 'comparacoes.php')[0]['comparacoes']
    vazios = {c['linha']: c['evidencia'] for c in todos if c['tipo'] == 'vazio'}     # a metade `== ''` e a que deixa de ser apontada
    assert 36 not in vazios and 37 not in vazios      # $w == 0 || $w == '' ; $w != '' && $w !== 0: o zero ja e tratado a parte
    assert 38 not in vazios and 39 not in vazios      # $w == '' ? 0 : $w ; ? '0' : $w : devolve 0 nos dois casos
    assert 41 not in vazios                           # $w != '' ? $w : 0
    assert 42 not in vazios                           # (int) $w == '' || (int) $w == 0
    assert vazios.get(40) == 'inteiro'                # ? 'x' : $w muda o resultado quando $w e 0
    assert 43 not in vazios                           # if ($w == '') { $w = 0; }: repete o zero, o resultado e o mesmo
    assert 44 not in vazios                           # is_string($w) && $w == '': o valor ja e garantidamente texto
    assert vazios.get(46) == ''                       # $a1 = $max + 1; $a1 == '': `+ 1` nao produz 0, entra so no nivel geral


def test_evidencia_nao_atravessa_case_diferente_nem_reatribuicao_nao_numerica_nem_date_menos_literal(roda):
    r = {c['linha']: c['evidencia'] for c in roda('comparacoes', 'comparacoes.php')[0]['comparacoes'] if c['tipo'] == 'vazio'}
    assert r[49] == ''        # $v1 = 0 no case 1; $v1 == '' no case 2: cases diferentes do mesmo switch nao se alcancam
    assert r[53] == ''        # $v2 = $n * 100; $v2 = str_pad(...): a reatribuicao nao numerica anula a evidencia
    assert r[55] == ''        # date('Y') - 1 nunca e 0


def test_atribuicao_em_ramo_anterior_do_mesmo_if_nao_chega_ao_elseif(roda):
    r = {c['linha']: c['evidencia'] for c in roda('comparacoes', 'comparacoes.php')[0]['comparacoes']}
    assert r[31] == ''                                    # if (..) { $r = 0; } elseif ($r == 't'): ramos exclusivos
    assert r[35] == 'inteiro'                             # if (..) { $w = 0; } if ($w == 't'): a atribuicao pode chegar
