# Área Assistência Social (branch `assistencia-social/migracao`)

### 📐 Dimensionada (11/11/2026)

Primeira área depois que as sete anteriores entraram na `base-php84` (PRs #2–#8). A branch **nasce da `base-php84`** (não da
área anterior) e segue o formato `area/assunto` do `CONTRIBUINDO.md` — decisão do usuário.

`scratchpad/dimensiona.py` (depois da Configuração): **57 telas de menu faltando** (68 no menu), 2 módulos (**Social** 44,
**Habitação** 13), **32 a alterar** só pelas telas (descontadas as 11 classes do falso positivo). **1 fantasma:**
`soc1_cidadao003.php`.

| Prefixo | Telas da área faltando | Outras áreas pendentes | Em disco | A alterar (só as telas) | A alterar (prefixo inteiro) |
|---|---|---|---|---|---|
| `soc` | 44 | — | 87 (`soc1_` 8, `soc2_` 42, `soc3_` 17, `soc4_` 20) | 4 | **9** |
| `hab` | 13 | — | 52 (`hab1_` 41, `hab2_` 2, `hab4_` 9) | 28 | **33** |

Nenhuma outra área pendente (Cidadão, Integrações, Gestor) usa `soc` ou `hab`. Hoje há **13 telas/abas `hab` no `map`**
(`hab1_workflow*` do Financeiro, `hab1_avaliacao*` da Configuração); com o prefixo inteiro no `location`, saem do `map`.

#### Divisão (aprovada pelo usuário, 11/11/2026)

**Um lote só: `soc` e `hab` inteiros pelo `location`** (~42 a alterar; 139 telas na bateria). As abas desses prefixos vão junto
com o `location`. Valem as regras de sempre: bateria do lote, bateria completa no fim da área, conferência pelo proxy, e o envio
(PR para a `base-php84`) só depois.

| Lote | Universo | Alterados | `php -l` 5.6/8.5 | Carga (LSP) | Classes | Escrita | Forma negada | **Bateria** |
|---|---|---|---|---|---|---|---|---|
| único `soc`+`hab` | 1.987 | 31 Rector + 3 à mão (2 em biblioteca compartilhada) | 1.987/1.987 | 371/371 (12 falham nos dois) | 803 (diffs só do harness) | 0 fora dos conhecidos | 2.210 pares, 0 div. | **138/139** (1 de ambiente) |

**Lote único — `soc` e `hab` inteiros** (139 arquivos; 11/11/2026). 48 alvos, 37 reais. `split()`: 92, todos `"#"`. Rector em
**31 arquivos**, só regras vetadas (22 guardas, 22 construtores, 22 `split`, 9 `parse_str`), 0 na 2ª passada; nenhuma
`OptionalParametersAfterRequired`. Remanescentes 0; lint 1.987/1.987 nos dois; portão 0; carga 371/371.

Bateria 137/139 → **138/139**. À mão:
- **`model/social/FamiliaRepository.model.php`:** `getInstance()` é `protected function` (não estática) e é chamado como estático
  pelos métodos `static` do repositório — aviso no 5.6, fatal no 8 (`soc2_beneficiosfamilia002`). Não usa `$this` → **`static`**
  (mesma correção do jpgraph no Financeiro).
- **`dbagata/classes/core/AgataQuery.class:95` — BIBLIOTECA COMPARTILHADA, defeito latente das áreas anteriores.**
  `($this->records <= ($this->Limit + $this->OffSet)) or ($this->Limit == 0)`: `Limit`/`OffSet` vêm do XML de cada relatório
  (`['Config']['Limit']`) e podem chegar `""`. No 8, `"" + ""` é `TypeError`; e, pior, **`"" == 0` é falso no 8 e verdadeiro no 5.6**
  (medido): consertar só a soma faria o relatório devolver **zero linhas em silêncio**. → `(int)` nos três (`(int)"" == 0` é
  verdadeiro nos dois). Qualquer relatório do dbagata sem limite no XML quebrava no 8.5; as baterias anteriores não passaram por
  nenhum por GET.
- **`dbagata/classes/pclzip/pclzip.lib.php:2381` — biblioteca compartilhada:** `@fread($v_file, $p_header['size'])` com tamanho 0
  (arquivo vazio indo para o ZIP): no 5.6 `false`, no 8 `ValueError` → `($p_header['size'] > 0 ? @fread(…) : false)`. Só este
  dos 32 `fread` do arquivo (o que apareceu).

**A 1 restante é de AMBIENTE, não de código:** `soc2_declaracaoinss002.php` gera um `.sxw` e o converte por
`model/configuracao/DocumentConverter.model.php`, que chama o comando `file` (tipo do arquivo) e o `soffice` (LibreOffice). **As
imagens têm as ferramentas trocadas:** a do 5.6 tem o LibreOffice (`libreoffice-writer` no Dockerfile) e **não tem `file`**; a do
8.5 tem `file` e **não tem LibreOffice**. O 5.6 para em "Falhou ao determinar o tipo de arquivo", o 8.5 em "Falhou em executar o
soffice" — nenhum dos dois gera o documento neste ambiente. **Pendência para o grupo:** a imagem do 8.5 sem LibreOffice faria
falhar, em produção, toda tela que converte documento (6 arquivos usam o `DocumentConverter`).

Bateria dirigida: dispensada — a **bateria completa** do fim da área (a seguir, pedida junto com o lote) cobre todas as telas
servidas, inclusive as que usam `dbagata/` e o `FamiliaRepository`.

Roteamento: **`soc|hab`** no `location`, na `FASE_A` e nos dois scripts; `map` regenerado → **1.307 entradas** (saíram as 6 telas
`hab` de menu que estavam nele: `hab1_avaliacao001/002/003`, `hab1_workflow001/002/003`). Conferido: `soc2_`, `/w/2/hab1_`,
`hab1_workflow001`, `Soc4_` → 8.5; `login`, `con1_` → 5.6. Passo 8b (84 telas da área no 8.5): nada indo ao 5.6. Pelo banco:
**67/67** telas de menu da Assistência Social em disco no 8.5 (+ 1 fantasma).

**Estado:** lote único concluído (commit local); bateria completa do fim da área em seguida (pedida junto).
