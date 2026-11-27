# Rastreador - taxa de parse da arvore (2026-11-27)

`nikic/php-parser` v4.19.1 (`ecidade/vendor`), modo `PREFER_PHP7`, executado no contêiner do PHP 8.5.12.

- Arquivos `.php` (sem `vendor/`, `tmp/`, `node_modules/`): **36712**
- Parseiam: **36701** (99.97%)
- Nao parseiam: **11**
- Tempo: 28.9 s (8 processos em paralelo)

Arquivo que nao parseia fica **sem sonda** (copiado como esta) e e registrado pelo instrumentador.

## Falhas

| Arquivo | Mensagem |
|---|---|
| `app/Domain/Patrimonial/Protocolo/Controller/Processo/AndamentoPadrao/CamposDinamicosRespostaController.php` | Syntax error, unexpected T_NAME_FULLY_QUALIFIED, expecting ';' on line 13 |
| `app/Domain/Patrimonial/Protocolo/Repository/Processo/AndamentoPadrao/CamposDinamicosRepository.php` | Syntax error, unexpected T_NAME_QUALIFIED, expecting '{' on line 7 |
| `app/Domain/Patrimonial/Protocolo/Transformers/Processo/AndamentoPadrao/CamposDinamicosResposta.php` | Syntax error, unexpected T_NAME_FULLY_QUALIFIED, expecting ';' on line 6 |
| `bib3_leitorcons002.php` | Syntax error, unexpected '}', expecting EOF on line 211 |
| `classes/db_cursoedu_ext_classe.php` | Syntax error, unexpected T_CLASS on line 31 |
| `edu1_diarioavaliacao001.php` | Syntax error, unexpected '<' on line 319 |
| `edu1_diarioavaliacaoobs001.php` | Syntax error, unexpected '<' on line 2 |
| `mer1_mer_desper_und003.php` | Syntax error, unexpected EOF on line 175 |
| `pes1_reajusteprog001.php` | Syntax error, unexpected '}', expecting EOF on line 132 |
| `src/Saude/Agendamento/Exame/Cota/Mensal/Municipio/Interface.php` | Syntax error, unexpected T_INTERFACE, expecting T_STRING on line 29 |
| `src/Saude/Agendamento/Exame/Cota/Mensal/Prestador/Interface.php` | Syntax error, unexpected T_INTERFACE, expecting T_STRING on line 29 |
