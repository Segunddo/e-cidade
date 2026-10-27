# Área Patrimonial (branch `4patrimonial-migrado`)

### 📐 Dimensionada e INICIADA (27/10/2026)

`scratchpad/dimensiona.py` refeito: **712 telas de menu faltando** (749 no menu, 6 fantasmas), universo 3.075,
873 já pagos, **469 a alterar** — os mesmos números de 22/10 (as 165 abas da 14ª lacuna não tocaram o universo de
Patrimonial).

8 módulos no banco: Compras 143 telas, Patrimônio 132, Protocolo 113, Veículos 113, Material 101, Licitações 84,
Contratos 63, Ouvidoria 32.

| Prefixo | Telas de Patrimonial no menu | Em outra área | Em disco | A alterar (prefixo inteiro) |
|---|---|---|---|---|
| `com` | 120 | 9 (Financeiro) | 372 | 204 |
| `pat` | 126 | 1 (Configuração) | 261 | 115 |
| `vei` | 113 | — | 172 | 155 |
| `lic` | 74 | 1 (RH, já no `map`) | 163 | 82 |
| `aco` / `ac` | 40 / 9 | — | 64 / 16 | 38 / 22 |
| `ouv` | 28 | — | 88 | 51 |
| `mat` | 95 | 26 (Configuração, Educação, Saúde) | 280 | via `map` |
| `pro` / `prot` | 69 / 16 | 39 / 7 | 337 / 48 | via `map` |
| `con` / `emp` / `cai` / `orc` / `cad` | 35 / 13 / 3 / 2 / 1 | Financeiro, Tributário… | — | via `map` |
| `func` / `processo` | 4 / 1 | — | — | via `map` |

**Escopo, o mesmo das três áreas anteriores:** Fase A = `ac`, `aco`, `ouv`, `lic`, `vei`, `pat`, `com` inteiros,
roteados por `location` (as poucas telas compartilhadas vão junto); Fase B = as telas de menu dos prefixos
compartilhados, pelo `map`. Ordem: do menor para o maior.

| Lote | Universo | Alterados | `php -l` 5.6/8.5 | Classes | Escrita | **Bateria** |
|---|---|---|---|---|---|---|
| `ac`+`aco`+`ouv` | 1.727 | 60 Rector + 8 à mão | 1.727/1.727 | 892, só artefatos conhecidos | 22.684 linhas, só artefatos conhecidos | **168/168** |

**Lote 1 — `ac`+`aco`+`ouv`** (Contratos e Ouvidoria, 168 telas). Rector só com regras já vetadas (37 guardas,
37 construtores, 32 `ereg`/`split` — os 143 `split` literais: 142 `"#"`, 1 `"/"` —, 23 `parse_str`+`extract`),
0 na 2ª passada. À mão:

- **`ouv1_cidadao.RPC.php`: 7 `break` fora de laço** (fatal de compilação no 8.5), todos no ramo de erro depois de
  `incluir()`/`alterar()` falhar — alcançáveis → **`exit;`** (o 5.6 morria ali). O `php -l` do 8.5 dirigiu um a um;
  os outros 6 `break` do arquivo estão dentro de `for` e ficaram.
- 4 guardas `pg_*` (`null`) pelo `guarda_ciclo.py`, em telas cujas SQL saem truncadas sem parâmetros (log do
  PostgreSQL: "erro de sintaxe no fim da entrada"); nenhuma variável guardada é comparada com `===`.
- `count(null)` → `count((array)…)` em `ouv1_prorrogacaoprazo003.php`.
- **`src/Patrimonial/Protocolo/Container.php:21`: `\ ECidade\V3\...`** (espaço depois da barra) — legal no 5.6,
  *parse error* no 8 (nome qualificado virou um token só). Espaço removido, mesmo significado. Achado pela
  bateria (`ouv4_solicitacaoprocessoeletronico.RPC.php`), **não** pelo `php -l` do universo — o arquivo não estava
  em universo nenhum: ver a **15ª lacuna** abaixo.

Classes: artefatos conhecidos (`lancamentoContabil`, `ordemPagamento`, `RequisicaoMaterial`, `empenho.php`
sem sessão) e um novo da mesma família, `solicitacaoCompra` (`.model.php` com argumento obrigatório no
construtor: o 5.6 segue com aviso, o 8.5 lança `ArgumentCountError` no harness). LSP entre arquivos
(`carrega_arquivo.php`, 215 com `extends`/`implements`): 204 OK nos dois, 11 falham igual nos dois.

Regressão: núcleo intocado; interseção com `con`/`prot`/`pro`/`cai` → as 244 telas desses prefixos no `map`:
**244/244**.
