# Estado compartilhado da equipe

`trabalho.json` diz **quem está mexendo em qual arquivo** e **o que já foi corrigido**. Ele vai no Git: é assim que
a equipe se coordena sem servidor central.

- **Não edite à mão.** Use as tools do MCP: `reivindicar_arquivo`, `liberar_arquivo`, `quadro`, `proximo_trabalho`.
- **Reivindicação expira** em 4 horas (mude com `ECIDADE_MCP_EXPIRA_HORAS`). Expirada, outra pessoa pode pegar o
  arquivo. Quem ainda está trabalhando renova chamando `reivindicar_arquivo` de novo.
- **Escrita segura**: o servidor trava o arquivo (`trabalho.json.lock`), grava num temporário e troca de uma vez
  (`os.replace`). Duas IAs na mesma máquina não perdem dados uma da outra.
- **Entre máquinas** a sincronização é o Git. Depois de reivindicar ou liberar, faça commit **só deste arquivo**:

  ```bash
  git add .mcp/estado/trabalho.json
  git commit -m "estado: reivindica ecidade/xxx.php"
  git pull --rebase && git push      # só quando a equipe combinar publicar
  ```

- **Conflito no Git?** O arquivo tem uma entrada por caminho, em ordem alfabética: mantenha as entradas dos dois
  lados, apague as marcas `<<<<<<<`, `=======`, `>>>>>>>` e faça commit. Enquanto houver marcas, as tools respondem
  `estado_corrompido` (de propósito: nada é sobrescrito).
- **Chave duplicada?** Um merge pode deixar o mesmo caminho duas vezes sem marca nenhuma (cada lado acrescentou a sua
  linha). O JSON comum ficaria só com a última e perderia a outra reivindicação calado; o servidor recusa com
  `estado_corrompido` e diz qual chave (`detalhes.chave_duplicada`). Combine com o colega qual entrada fica, apague a
  outra e faça commit só deste arquivo.
- **Permissão:** o servidor grava o arquivo com `0644` (legível por todos, como os demais arquivos do repositório).

Formato:

```json
{
  "versao": 1,
  "reivindicacoes": {"ecidade/tela001.php": {"quem": "ana", "motivo": "parse_str_1_arg", "desde": "…Z", "expira": "…Z"}},
  "concluidos":     {"ecidade/tela001.php": {"quem": "ana", "quando": "…Z", "padroes": ["parse_str_1_arg"], "observacao": ""}}
}
```
