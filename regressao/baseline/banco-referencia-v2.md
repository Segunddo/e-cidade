# Banco de referência v2 (dump com as migrations Laravel do PR)

Data: 2026-11-18. sha256 do dump: `972515745567622ce8394d91e63c481a50d3500104c115c170ba95544b8b0fad` (93.634.549 bytes),
registrado em `baseline.dump.sha256`. Cópia fora do git: `<seu-diretorio>/ecidade74-baseline-v2.dump`. O dump v1 (sha256
`15cd994a5326b3ec25c523f49f9ebe52f65e19d3ee3e58d715d625b2a10a444d`, cópia `<seu-diretorio>/ecidade74-baseline.dump`)
fica como histórico: nenhuma linha de base o usa mais.

## Por que mudou

O guia do grupo ("Migração do PHP 7.4 para o 8.5 a partir do PR #8", seção *Banco de dados* e decisão 1) diz que o
sistema do PR só monta o menu do Desktop com as migrations Laravel aplicadas, e que o dump de instalação não as tem.
Conferido ao vivo na referência (`ecidade74_php74`, :8074, dump v1) antes de mudar:

- o login abre o Desktop (`POST /v4/login` → `/extension/desktop`); instituições, áreas e módulos aparecem;
- **o clique num módulo não mostra itens**: `GET /extension/desktop/Menu/getItensMenu/` → **HTTP 500**; também 500 em
  `/v4/api/configuracao/menu/buscar-favoritos` e `/v4/api/configuracao/usuario/notificacoes`
  (`laravel.log`: não existem `configuracoes.itens_menu_usuario_favoritos` nem `notifications`);
- `public.migrations` tinha 456 linhas (a última de 2022-12-29); o `migrate:status` listava **736 pendentes**.

Sem menu, nenhuma tela abre pelo navegador: os fluxos não teriam o que medir. Aplicada a decisão **1(a)** do guia
(banco descartável, restaurado do dump de instalação, com as migrations rodando só nele, cópia guardada antes).

## Como foi feito

1. Runtimes do `e74` parados (nenhuma requisição HTTP no banco até o dump); banco restaurado do dump v1.
2. `php artisan migrate --force` (contêiner descartável com a imagem da referência, mesma rede e o mesmo `./ecidade`):
   **para na primeira migration** (`2019_04_16_132603_m13295_alteracoes_registro20`, chave duplicada em `db_syscampo`:
   o dump já tem o efeito dela, só não tem o registro em `public.migrations`).
3. Por isso as 736 pendentes rodaram **uma a uma, em ordem**, cada uma com `migrate --path=<arquivo>` (transação
   própria no PostgreSQL), seguindo para a próxima quando uma falha. A que falha é desfeita e **continua pendente**
   (não é marcada como rodada). Script fora do repositório; log por migration guardado com as saídas da task 4.
4. Resultado: **712 aplicadas, 24 falharam** (abaixo); `public.migrations` com 1.168 linhas. Criadas
   `configuracoes.itens_menu_usuario_favoritos`, `notifications` e a coluna `db_itensmenu.api`. Levou ~74 min (as
   migrations de dicionário de dados ligam um *event trigger* de DDL que deixa cada `ALTER/CREATE` lento).
5. Dump gerado logo em seguida (`gera_dump`), ainda sem HTTP; só então os runtimes voltaram.

Conferido depois: o menu monta (`getItensMenu` 200; favoritos e notificações 200) e os 6 fluxos de navegador abrem as
telas pelo Desktop (`regressao/completa/fluxos.py`).

## As 24 migrations que não aplicam no banco de instalação

São defeitos/descompassos **do PR** com o dump de instalação em PostgreSQL 16. Pela regra do grupo, ficam
**registrados, não corrigidos** (corrigir é decisão do grupo/da DBSeller):

| Causa | Qtde | Migrations |
|---|---|---|
| SQL com `\'` dentro de texto (só funciona com `standard_conforming_strings = off`; o PostgreSQL 16 usa `on`) | 14 | `M23983_correcao_atributo_fs_matriz`, `M23379_alteracao_calculo_alvara_vistoria`, `m24118_regras_documentos_virada_rp`, `M24845_FC_ISSQN`, `M25393_calculo_iptu_valenca`, `M25365_adiciona_desconto_isencoes_calculo`, `M25469_fc_issqn_verifica_isscadsimplesbaixa`, `M25430_unificacao_taxas_calculo_issqn`, `M25742_ajuste_pl_calculo_issqn`, `M26188_calculo_iptu_bage`, `M26136_ajuste_fc_issqn`, `M26991_calculo_fracionamento_iptu_valenca`, `m28074_adiciona_novos_documentos_transf_saldos`, `M27263_fc_issqn` |
| Dicionário de dados (`db_sysarqcamp`) apontando para registro inexistente | 4 | `m23809_adicionando_campo_is_classe_bilingue`, `m23809_removendo_campo_curso_profissionalizante_...`, `M25294_adicionar_campos_numpref`, `m27212_adicao_campos_para_transescolar_e_parametro_educacao` |
| Efeito já presente no dump (chave duplicada) | 2 | `2019_04_16 m13295_alteracoes_registro20`, `m26238_novo_parametro_altera_procedimento_avaliacao` |
| Objeto que o dump não tem / já tem | 3 | `M23082emissao_projeto_template` (visão `v_suplementacao_despesa`), `m23821_drop_db_tutorial` (tabela `db_tutorialetapapassos`), `M23625_acerto_recursos` (tabela de backup já existe) |
| Gatilho do banco falha durante a migration | 1 | `M24377_ajuste_cgmendereco` (`fc_issqn_atualiza_issbaseintegracaoexterna`: `EXECUTE` de texto nulo) |

**Efeito para a regressão:** as funções de cálculo do ISSQN/IPTU/alvará (`fc_issqn` e afins) ficam na versão do dump,
não na do PR. Telas e rotas que usam esses cálculos medem a referência **como ela está neste banco**; 7.4 e 8.5 usam o
mesmo banco, então a comparação continua justa, mas o comportamento não é necessariamente o de um banco de produção
migrado pela DBSeller (opção 1(b) do guia, se um dump oficial migrado aparecer).

## O que foi refeito por causa do dump novo

O sha256 mudou, então tudo que guarda o sha256 foi regravado **contra a referência**, com a proteção
`--confirmo-sobrescrever`: linha de base Laravel (`regressao/baseline/laravel/`) e fluxos (`regressao/baseline/fluxos/`),
cada uma com duas comparações seguidas idênticas; e os catálogos PHP foram reconferidos ao vivo. Números no
`regressao/README.md`.
