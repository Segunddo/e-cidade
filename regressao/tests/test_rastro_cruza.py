"""regressao/rastro/cruza.py: concordancia entre o backend de sondas (A) e o do Xdebug (B)."""
from regressao.rastro import cruza

A = """# Rastreador

## Defeitos (a resposta final difere): onde o dado se separou

### `t_igual.php`

**Linha causal:** `x.php:10` - o 7.4 so emite **aviso**

**Sintoma (onde a execucao estourou):** `x.php:12` - algo

### `t_mesmo_arquivo.php`

**Linha causal:** `y.php:5` - o 7.4 so emite **aviso**

### `t_so_a.php`

**Linha causal:** `z.php:1` - x

## Inconclusivos (nao contam como aprovados)

### `t_inconclusiva.php`

Nota: algo
"""

B = """# Rastreador

## Defeitos (a resposta final difere): onde o dado se separou

### `t_igual.php`

**Linha causal:** `x.php:10` - x

### `t_mesmo_arquivo.php`

**Linha causal:** `y.php:9` - x

### `t_so_b.php`

**Linha causal:** `w.php:3` - x

## Reconvergentes (o dado divergiu no meio, mas o resultado final e igual: correto)

### `t_so_a.php`

### `t_inconclusiva.php`
"""


def test_le_relatorio_extrai_veredito_causal_e_sintoma():
    r = cruza.le_relatorio(A)
    assert r["t_igual.php"] == dict(veredito="DIVERGE-CAUSAL", causal="x.php:10", sintoma="x.php:12")
    assert r["t_inconclusiva.php"]["veredito"] == "INCONCLUSIVO" and r["t_inconclusiva.php"]["causal"] is None


def test_classifica_a_concordancia_de_cada_tela():
    c = {l["tela"]: l["concordancia"] for l in cruza.cruza(cruza.le_relatorio(A), cruza.le_relatorio(B))}
    assert c["t_igual.php"] == "mesma-linha"
    assert c["t_mesmo_arquivo.php"] == "mesmo-arquivo"
    assert c["t_so_a.php"] == "so-A"
    assert c["t_so_b.php"] == "so-B"
    assert c["t_inconclusiva.php"] == "sem-causa"


def test_prefixo_de_caminho_nao_conta_como_arquivo_diferente():
    a = {"t.php": dict(veredito="DIVERGE-CAUSAL", causal="/var/www/html/vendor/x/Emulate.php:110", sintoma=None),
         "p.php": dict(veredito="DIVERGE-CAUSAL", causal="phar:///var/www/html/ext/P.phar/S.php:5", sintoma=None)}
    b = {"t.php": dict(veredito="DIVERGE-CAUSAL", causal="vendor/x/Emulate.php:110", sintoma=None),
         "p.php": dict(veredito="DIVERGE-CAUSAL", causal="phar://ext/P.phar/S.php:5", sintoma=None)}
    assert {l["tela"]: l["concordancia"] for l in cruza.cruza(a, b)} == {"t.php": "mesma-linha", "p.php": "mesma-linha"}


def test_resumo_conta_por_concordancia():
    r = cruza.resumo(cruza.cruza(cruza.le_relatorio(A), cruza.le_relatorio(B)))
    assert r == {"mesma-linha": 1, "mesmo-arquivo": 1, "so-A": 1, "so-B": 1, "sem-causa": 1}
