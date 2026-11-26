# Storage com os discos do PR no Laravel 13 (PHP8-77, 20/11/2026)

**Resumo:** esta medição repete a parte de arquivos da PHP8-77 (`php8-77-db-raw-storage.md`, *Arquivos*) com os
**discos do PR** e o vendor completo de cada trava:

- **7.4:** Laravel 8.73.2 e Flysystem 1.1.10;
- **8.5:** Laravel 13.43.0 e Flysystem 3.36.0.

Das 88 linhas de saída, 75 saem iguais. As 13 que diferem são 4 comportamentos do Flysystem 3, nos 3 discos locais,
e o disco `s3`, que não funciona em nenhum dos dois. Nenhuma das 13 é alcançada pelo código, então não houve correção.
Tudo rodou sem banco.

## Como foi medido

Trecho `scratchpad/php8_77_storage_l13.php`, pelo `docker/composer-85/roda-isolado.sh` (imagens de
`docker/php74-apache` e `docker/php85-apache`, `--network none`):

- Os discos vêm do `ecidade/configuration/filesystems.php` como está, lido pelo trecho: `local`, `public`,
  `templates_financeiro` e `s3`.
- O `storage_path()` aponta para uma pasta descartável em `/tmp`, pela raiz de um `Illuminate\Foundation\Application`
  sem inicializar.
- O `APP_URL` vem do `.env.example`, nos dois lados.
- Cada disco local passa por 27 operações; a facade `Storage` passa pelas 4 que o código usa.
- O texto gravado é ISO-8859-1, como no código.

```bash
VENDOR=<vendor do 7.4> bash docker/composer-85/roda-isolado.sh 7.4 scratchpad/php8_77_storage_l13.php > 74.txt
bash docker/composer-85/roda-isolado.sh 8.5 scratchpad/php8_77_storage_l13.php > 85.txt
diff 74.txt 85.txt | grep -c '^<'   # 13
```

O vendor do 7.4 vem do `composer install` do `ecidade/composer.lock` numa pasta à parte, com `dump-autoload` e
`ecidade/` montado em `/app`.

## Resultado (critério 2)

**Iguais (75 linhas):** nos 3 discos locais saem iguais:

- `root`, `exists`, `missing`, `put`, `get`, `size`, `lastModified`, `mimeType`, `path`, `url`;
- `files`, `allFiles`, `directories`, `append`, `prepend`;
- `copy` para destino novo, `move`, `makeDirectory`, `getVisibility`;
- `delete` e `deleteDirectory` de existente.

O `url` também sai igual nos 3: `local` dá `/storage/...`; `public` e `templates_financeiro` dão `APP_URL` mais o
caminho. Pela facade, `Storage::put`, `exists`, `path` e `delete` (disco padrão `local`) saem iguais.

**Diferentes (13 linhas):**

| Operação (em `local`, `public` e `templates_financeiro`) | 7.4 (Flysystem 1) | 8.5 (Flysystem 3) | Causa |
|---|---|---|---|
| `get` de arquivo inexistente | `FileNotFoundException` | `null` | guia 8 → 9, *Flysystem 3.x*: leitura que falha devolve `null` em vez de lançar, a menos que o disco tenha `'throw' => true` |
| `copy` para destino que já existe | `League\Flysystem\FileExistsException` | `true` (sobrescreve) | idem: escrita sobrescreve o que existe |
| `delete` de arquivo inexistente | `false` | `true` | idem (já medido na PHP8-77) |
| `deleteDirectory` de pasta inexistente | `false` | `true` | idem |
| disco `s3` | `Error: Class 'League\Flysystem\AwsS3v3\AwsS3Adapter' not found` | `Error: Class "League\Flysystem\AwsS3V3\PortableVisibilityConverter" not found` | o adaptador do S3 não está em nenhuma das travas: o disco não funciona nos dois, com o mesmo tipo de erro |

**O que o código alcança:** todos os usos de arquivo do código, conferidos com
`git ls-files -z -- '*.php' ':!vendor/' | xargs -0 grep -naP "Storage::|Contracts\\\\Filesystem|FilesystemManager|app\('filesystem'\)|->disk\(|League\\\\Flysystem"`
em `ecidade/`, são estes:

- `ApropriacaoDecimoFeriasService.php:371-399`: `exists`, `put`, `lastModified`, `delete`;
- `TriagemLaboratorialService.php:271`: `path`.

Os dois usam o disco padrão. Nenhum usa `get`, `copy`, `deleteDirectory`, outro disco ou o `s3`. O único que cai numa
diferença é o `delete` do arquivo de trava (`removeLock()`, linha 399), que ignora o retorno. A tela sai igual, então
não houve correção. Se algum código novo passar a depender da exceção do `get` ou do `copy`, `'throw' => true` no disco
devolve o lançamento da exceção. Isso é só do 8.5 e não foi aplicado, por não haver uso.

## Lacunas

- O app não foi inicializado: os discos vêm do arquivo de configuração lido direto. A inicialização no Laravel 13 é a
  PHP8-62 (`docs/migracao-laravel/laravel13-inicializacao.md`).
- Nada precisa de banco nesta parte.
