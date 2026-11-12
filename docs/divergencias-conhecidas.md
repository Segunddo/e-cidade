# Telas que divergem entre PHP 5.6 e PHP 8.5 na bateria

A bateria (`scratchpad/cmp.py`) abre **todo arquivo** dos prefixos servidos pelo PHP 8.5, **sem parâmetros**, nos dois runtimes,
e compara a saída byte a byte. Uma tela que sai diferente só pode ficar sem correção quando há um motivo comprovado de que **o uso
real não é afetado**. Esta é a lista das que sobram na bateria completa, com o motivo de cada uma.

Levantada em 12/11/2026, depois da Assistência Social. O detalhe de cada caso está no registro da área (coluna *Registro*).

## As categorias

| Categoria | O que significa | Afeta o usuário? |
|---|---|---|
| **Quebra nos dois** | A tela já é defeituosa no 5.6 (objeto nunca criado, função não carregada). O 8.5 quebra no mesmo ponto, às vezes com outra mensagem. | Não pela migração: já não funcionava. |
| **Fragmento** | Não é tela: é um pedaço de código incluído por outra tela, que nenhum menu abre. Aberto sozinho, falta o que a tela que o inclui prepara (conexão, objetos). A tela que o inclui sai idêntica. | Não. |
| **Sem parâmetro** | A bateria abre a tela sem os parâmetros que o uso real **sempre** passa (a tela anterior manda a data, o arquivo, o código). Testada com parâmetros reais, sai idêntica. | Não. |
| **Laço eterno no 5.6** | Sem parâmetro, o 5.6 entra num laço infinito (`while (!feof(false))`) e prende um processo; o 8.5 dá 500. A "correção fiel" reproduziria o laço. Com o parâmetro real, a tela funciona. | Não no uso real. |
| **Horário no PDF** | O relatório é igual; só muda o horário impresso no rodapé, que fica dentro do trecho comprimido do PDF (fora do alcance da normalização). Conferido descomprimindo. | Não. |
| **Dia da semana** | Sem parâmetro, `mktime(null)` vira **hoje** no PHP 8 (no 5.6, uma data fixa). Só diverge quando a bateria roda em fim de semana. | Não. |
| **Ambiente** | A diferença é das imagens Docker, não do código. | Sim, se a imagem for usada como está (ver a observação). |
| **⚠ REGRESSÃO** | Funciona no 5.6 e quebra no 8.5 **também no uso real**. Classificação antiga errada, achada em 12/11/2026. | **Sim — a corrigir.** |

## As telas

| Tela | Área | 5.6 | 8.5 | Categoria | Motivo | Registro |
|---|---|---|---|---|---|---|
| `iss1_tabalvara_depto001.php` | Tributário | 200 (formulário) | 500 | **⚠ REGRESSÃO** | Linha `$cltabdesc->k07_instit = …` com `$cltabdesc` nunca criado: o 5.6 cria o objeto sozinho (só um aviso) e monta a aba; o PHP 8 trata como erro fatal. Roda sempre, com ou sem parâmetro — conferido com `dbopcao=1` e `2`. Aberta como aba por `iss1_isstipoalvara002/003/005/006`. | `area-tributario.md` (classificada antes como "pré-existente") |
| `iss3_emissaoalvaraeventos001.php` | Tributário | 200 | 500 | **⚠ REGRESSÃO** | `pg_lo_export($oid, $arquivo, $conn)`: ordem de argumentos **antiga, que o PHP 5.6 aceita** (medido: exporta o arquivo certo); no PHP 8 é `ArgumentCountError`. Com um alvará existente, o 5.6 gera o documento e o 8.5 quebra. Aberta por `iss3_impressaoalvaraevento001` e `iss4_alvaraeventos001` com `?codigoAlvara=`. | `area-tributario.md` (classificada antes como "o 5.6 tolerava") |
| `iss4_issbasecaracteristicas001.php` | Tributário | 200 | 500 | Sem parâmetro | `$oGrupo` nulo quando aberta sozinha. Aberta por `iss1_issbase014`/`iss1_issbaseiframe` com `?q123_inscr=`; com o parâmetro, **idêntica**. | `area-tributario.md` |
| `agu1_aguaconsumo999.php` | Tributário | 200 (vazio) | 500 | Fragmento | Incluído por `agu1_aguaconsumo001/002/003` (idênticas). Sozinho, usa o banco sem conexão aberta: o 5.6 devolve página em branco, o 8.5 lança exceção. Não está no menu. | `area-tributario.md` |
| `agu4_cancelaleituras_classe.php` | Tributário | 302 (vazio) | 500 | Fragmento | Define a classe `cl_cancelaleituras`; incluído por `agu4_expdadoscoletores_003.php`. | `area-tributario.md` |
| `fis1_sanitario004.php` | Tributário | 500 | 500 | Quebra nos dois | Não tem nenhum `include` e usa `db_ancora()`/`rotulo->label()` sem carregá-los. O 5.6 morre com `Call to undefined function db_ancora()`. Não está no menu. | `area-tributario.md` |
| `bib1_emprestimo002.php` | Educação | 200 | 500 | Sem parâmetro | Iframe que calcula a data de devolução; sem `ano/mes/dia`, o `mktime()` recebe `"--"`. Com 5 datas reais (dia útil, sábado, domingo, Páscoa, 31/12), **idêntica**. | `area-educacao.md` |
| `bib2_comprovantemodelo_80mm.php`, `bib2_comprovantemodelo_a4.php` | Educação | 200 | 500 | Fragmento | Incluídos por `bib2_emprestimo002.php` (idêntica). | `area-educacao.md` |
| `edu1_calendarioescola002/003.php`, `edu1_escolabase002/003.php`, `edu1_procescola002/003.php` | Educação | 500 | 500 | Quebra nos dois | Objeto nunca instanciado (`$clcalendarioescola`, `$clescolabase`, `$clprocescola`). | `area-educacao.md` |
| 8 telas do Censo/INEP: `edu4_exportarsituacaoaluno002`, `edu4_importacaoatualizacaoaluno002`, `edu4_importarcodigoinep002`, `edu4_importarcodigoinep_2009_002`, `edu4_importarmatriculainep002`, `edu4_atualizacadastrocenso002`, `edu4_atualizacadastrocenso_2009_002`, `edu4_verifexportcenso002` | Educação | laço eterno (ou 500) | 500 | Laço eterno no 5.6 | Sem o caminho do arquivo, `fopen` devolve `false` e `while (!feof(false))` não termina no 5.6 (um processo ficou 32 min a 100% de CPU). No uso real, a tela anterior passa o arquivo. Na bateria aparecem como divergência ou como *timeout*, conforme o tempo. | `area-educacao.md` |
| `rec2_espelhoponto002.php` | Recursos Humanos | laço eterno | 500 | Laço eterno no 5.6 | Mesma causa: `fopen` de `tmp/dados_espelho_ponto_{id}.txt` sem o `id`. | `area-recursos-humanos.md` |
| `cai2_receisub002.php` | Financeiro | 500 (vazio) | 500 | Quebra nos dois | `$clagata->api` com `$clagata` nunca criado (conferido: `NULL` nos dois). | `area-financeiro.md` |
| `orc1_orcsuplem005.php` | Financeiro | 500 | 500 | Quebra nos dois | `forms/db_frmorcsuplem.php:90` chama `$clorcprojeto->sql_record()` sem que `$clorcprojeto` seja criado. Saída igual até o erro. | `area-financeiro.md` |
| `orc2_orcprevmensalrec002.php`, `orc2_receitasDespesasPrevidenciariasServidores002.php` | Financeiro | 200 | 200 | Horário no PDF | Só o horário do rodapé muda. A segunda é intermitente (aparece quando as duas requisições caem em segundos diferentes). | `area-financeiro.md` |
| `lab2_mapacoletaconsulta.php` | Saúde | 200 (vazio) | 500 | Sem parâmetro | `mktime()` recebe `""` sem as datas. O formulário (`lab2_mapacoleta001`) exige período e laboratório; com parâmetros reais, 5 casos **idênticos**. | `area-saude.md` |
| `lab4_resultadomodelo1.php` | Saúde | 200 | 500 | Fragmento | Incluído por `lab4_emissaoresultnovo002.php:603` (idêntica), que define `$oDadosEstrutura`. | `area-saude.md` |
| `sau2_bpa001.php` | Saúde | 200 | 500 | Sem parâmetro | Sem `?bpa=`, `file("")`. As 3 chamadoras sempre passam o arquivo de validação; com 2 arquivos reais, **idêntica**. | `area-saude.md` |
| `mer_subitem004.php` | Educação | 200 | 200 | Dia da semana | `date("w", mktime(0,0,0,$mes,$dia,$ano))` sem parâmetros: o PHP 8 usa hoje. Só diverge em sábado/domingo. As 3 chamadas reais mandam a data completa; com 4 datas reais, **idêntica**. | `area-saude.md` |
| `sys3_modulos002.php` | Configuração | 200 | 200 | Horário no PDF | PDF de 813 páginas; descomprimidas, **0 linhas diferentes fora do rodapé**. | `area-configuracao.md` |
| `sys4_consultaXML.RPC.php` | Configuração | 200 (vazio) | 500 | Sem parâmetro | `file_get_contents("")` sem `sUrl`. A única chamadora (`scripts/classes/dbXmlEditor.js`) sempre manda `sUrl`; com um XML real, **idêntica**. | `area-configuracao.md` |
| `soc2_declaracaoinss002.php` | Assistência Social | 200 (mensagem de erro) | 200 (outra mensagem de erro) | Ambiente | O relatório converte um documento usando o comando `file` e o LibreOffice. A imagem do 5.6 tem o LibreOffice e não tem `file`; a do 8.5 tem `file` e não tem o LibreOffice. Nenhum dos dois gera o documento aqui. | `area-assistencia-social.md` |

## Observações

- **Ambiente:** com a imagem do PHP 8.5 como está, **toda tela que converte documento** falharia em produção (6 arquivos usam
  `model/configuracao/DocumentConverter.model.php`). A imagem precisa do `libreoffice-writer`, como a do 5.6.
- **As duas regressões** foram classificadas na migração do Tributário como "bug pré-existente". A revisão desta tabela mostrou que
  o 5.6 **funcionava** nas duas. A correção fiel é a de sempre: reproduzir o que o 5.6 fazia (criar o objeto que ele criava
  sozinho; chamar `pg_lo_export` na ordem que o PHP 8 aceita).
- **Telas fora desta lista** que não são servidas pelo 8.5 (por exemplo, as janelas de pesquisa `func_`) não entram na bateria; ver a
  frente das `func_` em `docs/registro/dimensionamento.md`.
