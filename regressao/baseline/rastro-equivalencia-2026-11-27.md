# Rastreador - portao de equivalencia (2026-11-27)

Pergunta: a arvore instrumentada (porta 8091) responde **igual** a normal (porta 80)? Sem isso o rastreador nao vale nada.

- Amostra: **200 telas** sorteadas com semente fixa (7) entre todas as telas da raiz, em **cada** um dos dois PHP (7.4 e 8.5)
- Comparacao: codigo HTTP + resposta normalizada (mesma normalizacao da bateria; a porta do vhost na pagina de erro e ignorada)
- **Diferentes: 0** (lista vazia = portao aprovado)
- Instaveis (a propria resposta normal muda entre duas leituras, entao nao ha como comparar): 6

  - `cai3_iptupago002.php` em `ecidade74_php74`
  - `cai3_iptupago002.php` em `ecidade74_php85`
  - `con2_contrans002.php` em `ecidade74_php85`
  - `con2_departusu002.php` em `ecidade74_php74`
  - `pes2_araconferencias002.php` em `ecidade74_php74`
  - `pes2_araconferencias002.php` em `ecidade74_php85`

## O que o portao ja pegou

1. **Handler de erros:** o `rt.php` repassava 4 argumentos ao handler da aplicacao, que no 7.4 exige 5 (`$errcontext`): `ArgumentCountError`. Corrigido repassando exatamente o que o PHP entregou.
2. **Mascara do handler:** o handler da aplicacao so recebe erros fora de NOTICE/WARNING/DEPRECATED/STRICT (`php.error_reporting`); o `rt.php` o chamava para todos. Corrigido respeitando a mascara (22517, conferida contra as constantes do PHP nos dois contêineres).
3. **`pre1_leis001.php`:** a tela confere o modo (0754) dos arquivos de `bin/` e lista os que nao o tem. A copia instrumentada perdia o modo e tinha arquivos a mais (`.map.json`, `rt.php`). Corrigido preservando o modo e movendo mapas e `rt.php` para fora da arvore. Primeira passada do portao: 2 diferencas (esta tela, nos dois PHP); depois da correcao: 0.

Fora o portao, a medicao da arvore achou a divisao sem espaco (`$a/count($b)` virando comentario de linha); ver `rastro-arvore-2026-11-27.md`.
