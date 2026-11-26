#!/usr/bin/env python3
# PHP8-62 (T-151): cobertura do inventario 8 -> 13 (docs/migracao-laravel/inventario-8-a-13-itens.tsv): cada item em uso x tarefa do quadro que mede/cobre.
# Uso (raiz do repositorio):  python3 scratchpad/cobertura_inventario.py [--escreve]
#   sem argumento: confere que os 47 itens USA/MANUAL do inventario estao na tabela abaixo (versao, item, contagens) e imprime o resumo;
#   --escreve: regrava docs/migracao-laravel/cobertura-inventario-8-a-13.tsv.
import csv, collections, sys
INV = 'docs/migracao-laravel/inventario-8-a-13-itens.tsv'
OCO = 'docs/migracao-laravel/inventario-8-a-13-ocorrencias.tsv'
SAIDA = 'docs/migracao-laravel/cobertura-inventario-8-a-13.tsv'
# situacao: COBERTO (tarefa mede o item), SEM EFEITO (lido/medido: o que o guia muda nao ocorre no codigo), MANUAL (item sem lista de quebras: diff do esqueleto), BANCO (so da para medir com banco), SEM TAREFA
# estado das tarefas em 20/11/2026 (quadro): F=Feito, QA, R=Revisao, D=Fazendo, S=na fila (Sprint Backlog)
M = [
 ('9.x', 'Exception Handler Contract Binding', 'COBERTO', 'T-143 (QA); T-129 (F)', 'o app do PR sobe no 13 com o Handler (boot, render JSON e redirecionamento); config de erros', 'baixo', ''),
 ('9.x', 'Belongs To Many firstOrNew, firstOrCreate, and updateOrCreate Methods', 'SEM EFEITO', '', 'o uso (`BaseDisciplinaRepository.php:29`, `$this->newQuery()->updateOrCreate(`) e do model, nao de relacao BelongsToMany (o item muda so as relacoes)', 'nenhum', 'leitura do arquivo'),
 ('9.x', 'The FILESYSTEM_DRIVER Environment Variable', 'COBERTO', 'T-149 (R)', 'disks do PR (put/get/exists/url/delete) em pasta temporaria; o PR le `FILESYSTEM_DRIVER` no proprio `configuration/filesystems.php:16`', 'baixo', ''),
 ('9.x', 'Flysystem 3.x', 'COBERTO', 'T-111 (F); T-149 (R)', 'Storage:: em pasta descartavel 7.4 x 8.5 (L8); repete no L13', 'baixo', ''),
 ('9.x', 'Overwriting Existing Files', 'COBERTO', 'T-111 (F); T-149 (R)', 'idem (sobrescrever arquivo)', 'baixo', ''),
 ('9.x', 'Write Exceptions', 'COBERTO', 'T-111 (F); T-149 (R)', 'idem (falha de escrita devolve false x lanca)', 'baixo', ''),
 ('9.x', 'Deleting Missing Files', 'COBERTO', 'T-111 (F); T-149 (R)', 'idem (`delete` de inexistente)', 'baixo', ''),
 ('9.x', 'The when / unless Methods', 'SEM EFEITO', '', 'o guia 9 so muda quando o 1o argumento e uma Closure (passa a ser executada); 0 das 231 chamadas usam Closure como condicao (comando no doc)', 'nenhum', 'medido por leitura'),
 ('9.x', 'The opis/closure Library', 'COBERTO', 'T-119 (F); T-131 (D); T-145 (S)', 'resolucao do pacote (T-119) e payload serializado dos jobs (T-131/T-145)', 'baixo', ''),
 ('9.x', 'Unvalidated Array Keys', 'COBERTO', 'T-109 (F); T-133 (R)', '1.350 casos de form request e 348 regra x valor, 7.4 x 8.5 (L8) e repetidos no L13', 'baixo', ''),
 ('9.x', 'Miscellaneous', 'MANUAL', 'T-143 (QA) indireta', 'MANUAL: so remete ao diff do esqueleto `laravel/laravel`; o PR nao usa o esqueleto novo; sem lista de quebras', 'baixo', 'sem codigo proprio a medir'),
 ('10.x', 'Minimum Stability', 'COBERTO', 'T-119 (F)', 'composer-85.json/lock resolvem sobre o Laravel 13 (`composer.json:96` do PR nao muda)', 'nenhum', ''),
 ('10.x', 'The registerPolicies Method', 'COBERTO', 'T-135 (D); T-143 (QA)', 'AuthServiceProvider (patches do Passport 13 e boot do app)', 'baixo', ''),
 ('10.x', 'Database Expressions', 'COBERTO', 'T-111 (F); T-125 (QA)', '302 DB::raw classificados pelo Grammar; os 23 que quebram no 10+ ajustados', 'baixo', ''),
 ('10.x', 'ULID Columns', 'SEM EFEITO', '', 'o item e `->ulid()` sem argumento; o codigo tem `->uuid(\'id\')` (`2022_10_24_103009_create_notifications_table.php:17`), que nao muda', 'nenhum', 'leitura do arquivo'),
 ('10.x', 'Monolog 3', 'COBERTO', 'T-153 (S)', 'canais de `configuration/logging.php`, formato da linha e nivel com Monolog 3', 'baixo', ''),
 ('10.x', 'The dispatch() Helper Return Value', 'SEM EFEITO', 'T-145 (S) repete os jobs', 'as 12 chamadas sao instrucoes (`dispatch(new Job(...));`); o valor devolvido nao e usado', 'nenhum', 'leitura das 12 linhas'),
 ('10.x', 'Middleware Aliases', 'COBERTO', 'T-140 (R)', '`app/Http/Kernel.php:74`: o Kernel do 13 ainda le `$routeMiddleware`; classes dos aliases conferidas', 'baixo', ''),
 ('10.x', 'Service Mocking', 'COBERTO', 'T-108 (QA); T-137 (R)', 'testes proprios (`tests/TestCase.php`, `tests/Unit/...`) com Mockery/PHPUnit novos', 'baixo', ''),
 ('10.x', 'Closure Validation Rule Messages', 'COBERTO', 'T-133 (R)', 'regras com Closure de `TriagemLaboratorialRequest.php:59-86` entre os casos de form request', 'baixo', ''),
 ('10.x', 'Validation Messages and Closure Rules', 'COBERTO', 'T-133 (R)', 'idem', 'baixo', ''),
 ('10.x', 'Miscellaneous', 'MANUAL', 'T-143 (QA) indireta', 'MANUAL: diff do esqueleto; sem lista', 'baixo', ''),
 ('11.x', 'Application Structure', 'COBERTO', 'T-140 (R); T-145 (S)', '`app/Http/Kernel.php` (propriedades e classes, medido) e `app/Console/Kernel.php` (agendamento)', 'baixo', ''),
 ('11.x', 'Password Rehashing', 'SEM EFEITO', '', 'o unico uso e o scaffold `RegisterController.php:68` (`bcrypt`), sem rota que o chame; o login do PR e do Passport (T-135)', 'nenhum', 'leitura; sem `Auth::routes()`'),
 ('11.x', 'The AuthenticationException Class', 'COBERTO', 'T-128 (QA); T-147 (S)', '401 sem token nas rotas /v4 (`Handler::unauthenticated`)', 'baixo', ''),
 ('11.x', 'Cache Key Prefixes', 'COBERTO', 'T-152 (S)', 'prefixo padrao do cache que mudou no 11 (chaves iguais ao 7.4)', 'medio', 'o 7.4 e o 8.5 podem compartilhar cache'),
 ('11.x', 'Eloquent Model casts Method', 'COBERTO', 'T-124 (F); T-146 (R)', '58 `$casts =` (propriedade, continua valendo); os 58 models carregam no 13 sem conflito', 'nenhum', ''),
 ('11.x', 'Modifying Columns', 'SEM TAREFA', '', '`->change()` em 2 migrations (`2021_10_25_083540_alter_secret_to_oauth_clients.php:17,29`; `2024_08_13_093320_M28685_ajuste_schema_tabela_mensageriaacordo.php:243`): no 11+ nao ha DBAL e o `change()` tem de repetir todos os modificadores da coluna', 'medio', 'instalacao do zero roda as migrations; dá para compilar o SQL pelo Grammar sem banco'),
 ('11.x', 'Floating-Point Types', 'SEM TAREFA', '', '`float`/`double` com argumentos em 14 chamadas de 5 migrations (ex.: `2021_12_14_114408_M19629_create_pix_tipo_debito.php:23`, `double(8,2)`): o 11 reescreveu esses tipos; no PostgreSQL ambos viram `double precision`/`float(53)`, mas nao foi medido', 'baixo', 'compilar o SQL pelo Grammar sem banco'),
 ('11.x', 'Doctrine DBAL Removal', 'COBERTO', 'T-119 (F)', '`doctrine/dbal` saiu do composer-85 (nenhum `Doctrine\\DBAL` no codigo; o uso indireto e o `->change()` acima)', 'baixo', 'o `change()` esta em "Modifying Columns"'),
 ('11.x', 'Carbon 3', 'COBERTO', 'T-134 (F); T-144 (D)', '275 linhas medidas com a entrada real; patches propostos e sendo aplicados no 13', 'medio', ''),
 ('11.x', 'Synchronous Jobs in Database Transactions', 'COBERTO', 'T-145 (S); T-131 (D)', '`configuration/queue.php:18,33,34` (`sync`, `after_commit`); jobs e config de fila no 13', 'baixo', ''),
 ('11.x', 'Updating Passport', 'COBERTO', 'T-130 (F); T-135 (D)', 'Passport 13: 14 pontos (login, `Passport::routes()`, `CheckClientCredentials`...)', 'alto', ''),
 ('11.x', 'Miscellaneous', 'MANUAL', 'T-143 (QA) indireta', 'MANUAL: diff do esqueleto; sem lista', 'baixo', ''),
 ('12.x', 'Carbon 3', 'COBERTO', 'T-134 (F); T-144 (D)', 'mesmo item do 11.x', 'medio', ''),
 ('12.x', 'Container Class Dependency Resolution', 'SEM EFEITO', '', 'o padrao `->make(` casa metodos `make` de repositorios (6 das 8); os 2 do container sao `$app->make(Console\\Kernel::class)` (`ProcessoService.php:629`, `NotificarTransferenciaProcessoService.php:40`), sem parametro com valor padrao', 'nenhum', 'leitura das 8 linhas'),
 ('12.x', 'Nested Array Request Merging', 'COBERTO', 'T-140 (R)', '`DBRequestMiddleware.php:30` (casos com arrays aninhados, iguais ao 7.4); `SessionMiddleware.php:51` depende de banco', 'baixo', 'SessionMiddleware: banco'),
 ('12.x', 'Route Precedence', 'COBERTO', 'T-118 (F); T-147 (S)', '1.425 rotas vivas, 27 pares repetidos (vence a ultima no 8 e no 12+)', 'baixo', ''),
 ('12.x', 'Local Filesystem Disk Default Root Path', 'COBERTO', 'T-149 (R)', '`configuration/filesystems.php:48,53,60` (root dos discos)', 'baixo', ''),
 ('12.x', 'Miscellaneous', 'MANUAL', 'T-143 (QA) indireta', 'MANUAL: diff do esqueleto; sem lista', 'baixo', ''),
 ('13.x', 'Cache Prefixes and Session Cookie Names', 'COBERTO', 'T-152 (S); T-140 (R)', 'cookie `laravel_session` medido (igual; `same_site` corrigido); prefixo do cache em `configuration/cache.php:97`; os 4 de `database.php` sao `prefix` de conexao', 'baixo', ''),
 ('13.x', 'Collection Model Serialization Restores Eager-Loaded Relations', 'BANCO', 'T-131 (D); T-145 (S) so o payload', '40 usos em 20 arquivos (`SerializesModels`): o payload e medido sem banco; restaurar as relacoes ao reler o model exige banco', 'medio', 'fica para quando houver decisao sobre banco'),
 ('13.x', 'Default Password Reset Subject', 'COBERTO', 'T-150 (S)', '`ResetPasswordController.php:8`: assunto do e-mail de redefinicao no Symfony Mailer (transporte `array`)', 'baixo', ''),
 ('13.x', 'Queued Notifications and Missing Models', 'BANCO', 'T-145 (S); T-150 (S) so o render', '18 notificacoes na fila: o descarte quando o model nao existe mais exige banco', 'medio', 'fica para quando houver decisao sobre banco'),
 ('13.x', 'withScheduling Registration Timing', 'COBERTO', 'T-145 (S)', '`app/Console/Kernel.php:51` (agendamento)', 'baixo', ''),
 ('13.x', 'Request Forgery Protection', 'COBERTO', 'T-140 (R)', '`VerifyCsrfToken` e `Kernel.php:52`: POST sem token e com token invalido iguais ao 7.4', 'baixo', ''),
 ('13.x', 'Miscellaneous', 'MANUAL', 'T-143 (QA) indireta', 'MANUAL: diff do esqueleto; sem lista', 'baixo', ''),
]
inv = list(csv.reader(open(INV, encoding='utf-8'), delimiter='\t'))
alvo = []
for r in inv[1:]:
    r = r + [''] * (9 - len(r))
    if r[2] in ('USA', 'MANUAL'):
        alvo.append((r[0], r[1], r[2], r[3], r[4]))
oco = collections.defaultdict(list)
for r in list(csv.reader(open(OCO, encoding='utf-8'), delimiter='\t'))[1:]:
    oco[(r[0], r[1])].append(r[3])
chaves = [(a, b) for a, b, *_ in M]
assert len(M) == len(alvo) == 47, (len(M), len(alvo))
assert collections.Counter(chaves) == collections.Counter((a[0], a[1]) for a in alvo), 'itens do inventario x tabela'
cont = collections.Counter(m[2] for m in M)
if '--escreve' in sys.argv:
    inv_cnt = {(a[0], a[1], i): a for i, a in enumerate(alvo)}
    with open(SAIDA, 'w', encoding='utf-8') as o:
        w = csv.writer(o, delimiter='\t', lineterminator='\n')
        w.writerow(['versao', 'item do guia', 'resultado', 'ocorrencias', 'arquivos', 'exemplos (arquivo:linha)', 'situacao', 'tarefas', 'o que cobre / por que', 'risco', 'nota'])
        usados = collections.Counter()
        for m in M:
            k = (m[0], m[1]); i = usados[k]; usados[k] += 1
            cand = [a for a in alvo if (a[0], a[1]) == k][i]
            ex = '; '.join(oco[k][:3])
            w.writerow([m[0], m[1], cand[2], cand[3], cand[4], ex, m[2], m[3], m[4], m[5], m[6]])
if '--when' in sys.argv:   # 'The when / unless Methods' (9.x): so muda quando o 1o argumento e uma Closure; conta as chamadas com Closure como condicao
    import re
    tot = fecha = 0
    for ref in oco[('9.x', 'The when / unless Methods')]:
        f, l = ref.rsplit(':', 1)
        L = open('ecidade/' + f, encoding='latin-1').read().split('\n'); i = int(l) - 1
        m = re.search(r'->(when|unless)\(\s*(.{0,40})', ' '.join(x.strip() for x in L[i:i + 3]))
        if m:
            tot += 1
            if re.match(r'(static\s+)?(function|fn)\b', m.group(2)): fecha += 1
    print('when/unless: %d chamadas, %d com Closure como condicao' % (tot, fecha))
print('itens:', len(M), dict(cont))
cob = [m for m in M if m[2] == 'COBERTO']
todas_f = [m for m in cob if all('(F)' in t for t in m[3].split(';'))]
na_fila = [m for m in cob if '(S)' in m[3]]
print('COBERTO: %d; todas as tarefas Feitas: %d; ao menos uma tarefa ainda na fila (S): %d; as outras (Revisao/QA/Fazendo): %d' % (len(cob), len(todas_f), len(na_fila), len(cob) - len(todas_f) - len(na_fila)))
print('USA:', sum(1 for a in alvo if a[2] == 'USA'), 'MANUAL:', sum(1 for a in alvo if a[2] == 'MANUAL'))
