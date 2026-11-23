"""Inventario de rotas: Laravel 8 (`artisan route:list --json`, inclui rest/v1) e Silex api/V1.

O `route:list` do Laravel 8 INSTANCIA cada controller para juntar o middleware dele
(`Route::gatherMiddleware` -> `controllerMiddleware`): um unico controller que nao constroi no console
da referencia (classe inexistente, modelo `cl_*` do legado que so o request carrega...) derruba a listagem
inteira. Quando isso acontece, o inventario usa uma listagem TOLERANTE com o mesmo formato (mesmo
`getRouteInformation` do comando, com `flushMiddlewareGroups`), que captura o erro POR ROTA: a rota continua
no inventario (vira caso normal; pela HTTP ela pode funcionar ou dar 500) e o erro vai para a coluna
`erro_controller`.
"""
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from regressao.nucleo.ambiente import containers_do_ambiente

DIR_APP = "/var/www/html"
ARQ_INVENTARIO = Path(__file__).resolve().parent / "casos" / "_inventario.tsv"
ORIGENS = ("laravel", "rest", "silex")
TIMEOUT_LISTAGEM = 300
LIMITE_ERRO = 200
COLUNAS_TSV = ("metodo", "uri", "middleware", "action", "origem", "erro_controller")

# Mesma informacao de RouteListCommand::getRouteInformation (Laravel 8.73), com o erro por rota.
SCRIPT_TOLERANTE = r"""<?php
require getcwd() . '/vendor/autoload.php';
$app = require getcwd() . '/bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
$router = $app['router'];
$router->flushMiddlewareGroups();
$saida = [];
foreach ($router->getRoutes() as $route) {
    $erro = null;
    try {
        $mw = $router->gatherRouteMiddleware($route);
    } catch (Throwable $e) {
        $mw = $route->middleware();
        $erro = get_class($e) . ': ' . $e->getMessage();
    }
    $mw = array_map(function ($m) { return $m instanceof Closure ? 'Closure' : $m; }, $mw);
    $saida[] = [
        'domain' => $route->domain(),
        'method' => implode('|', $route->methods()),
        'uri' => $route->uri(),
        'name' => $route->getName(),
        'action' => ltrim($route->getActionName(), '\\'),
        'middleware' => implode("\n", $mw),
        'erro' => $erro,
    ];
}
echo json_encode($saida);
"""


class ErroInventario(RuntimeError):
    """Nao foi possivel listar as rotas da referencia."""


@dataclass
class Rota:
    metodo: str
    caminho: str
    middleware: list[str]
    controller: str
    origem: str  # "laravel" | "rest" | "silex"
    erro: str = ""  # controller que nao instancia na referencia (listagem tolerante)


def _limpa_erro(erro) -> str:
    return re.sub(r"\s+", " ", str(erro or "")).strip()[:LIMITE_ERRO]


def parseia_route_list_json(texto: str) -> list[Rota]:
    """Saida de `route:list --json` (Laravel 8: lista de {domain, method, uri, name, action, middleware};
    middleware separado por quebra de linha) ou da listagem tolerante (mais a chave `erro`)."""
    try:
        dados = json.loads(texto)
    except ValueError:
        raise ErroInventario(f"saida do route:list nao e JSON: {texto.strip()[:150]!r}") from None
    if not isinstance(dados, list):
        raise ErroInventario("saida do route:list nao e uma lista de rotas")
    rotas: list[Rota] = []
    for d in dados:
        caminho = "/" + str(d["uri"]).lstrip("/")
        mw = [m.strip() for m in str(d.get("middleware") or "").split("\n") if m.strip()]
        origem = "rest" if caminho.startswith("/rest/") else "laravel"
        rotas.append(Rota(str(d["method"]), caminho, mw, str(d.get("action") or ""), origem,
                          _limpa_erro(d.get("erro"))))
    return rotas


def _roda(cmd: list[str], entrada: bytes | None = None):
    try:
        return subprocess.run(cmd, input=entrada, capture_output=True, timeout=TIMEOUT_LISTAGEM)
    except (OSError, subprocess.SubprocessError) as e:
        raise ErroInventario(f"docker indisponivel ({type(e).__name__})") from None


def rotas_laravel(runner=None) -> tuple[list[Rota], str]:
    """(rotas, fonte) da referencia (container `containers_do_ambiente().ref`). Fonte e
    `route:list --json` ou, se ele falhar, `tolerante (...)` com o motivo."""
    runner = runner or _roda
    container = containers_do_ambiente().ref
    r = runner(["docker", "exec", "-w", DIR_APP, container, "php", "artisan", "route:list", "--json"])
    if r.returncode == 0:
        try:
            return parseia_route_list_json((r.stdout or b"").decode("utf-8", errors="replace")), "route:list --json"
        except ErroInventario:
            pass
    motivo = _limpa_erro((r.stderr or b"").decode("utf-8", errors="replace") or f"codigo {r.returncode}")
    t = runner(["docker", "exec", "-i", "-w", DIR_APP, container, "php", "-d", "display_errors=stderr"],
               SCRIPT_TOLERANTE.encode("utf-8"))
    if t.returncode != 0:
        raise ErroInventario(f"route:list falhou ({motivo}) e a listagem tolerante tambem (codigo {t.returncode}): "
                             + _limpa_erro((t.stderr or b"").decode("utf-8", errors="replace")))
    return (parseia_route_list_json((t.stdout or b"").decode("utf-8", errors="replace")),
            f"tolerante (route:list --json falhou: {motivo})")


_MOUNT = re.compile(r"""->mount\(\s*\$prefix\s*\.\s*['"]([^'"]*)['"]\s*,\s*new\s+(\w+)""")
_VERBO = re.compile(
    r"""\$\w+->(get|post|put|delete|patch|match)\(\s*['"]([^'"]*)['"]\s*,\s*['"]([^'"]*)['"]""")
_PREFIXO_API = "/api/v1"


def varre_silex(raiz: Path) -> list[Rota]:
    api = Path(raiz) / "ecidade" / "api" / "V1"
    try:
        prov = (api / "APIServiceProvider.php").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    montagem = {cls: pref for pref, cls in _MOUNT.findall(prov)}
    rotas: list[Rota] = []
    for arq in sorted((api / "Providers" / "Controller").glob("*.php")):
        pref = montagem.get(arq.stem)
        if pref is None:
            continue
        for verbo, caminho, handler in _VERBO.findall(arq.read_text(encoding="utf-8", errors="replace")):
            completo = _PREFIXO_API + pref + "/" + caminho.lstrip("/")
            rotas.append(Rota(verbo.upper(), completo, ["silex"], handler, "silex"))
    return sorted(rotas, key=_chave)


def _chave(r: Rota):
    return (r.origem, r.caminho, r.metodo, r.controller, ",".join(r.middleware))


def grava_tsv(rotas: list[Rota], destino: Path = ARQ_INVENTARIO) -> None:
    linhas = ["\t".join(COLUNAS_TSV)]
    for r in sorted(rotas, key=_chave):
        linhas.append("\t".join([r.metodo, r.caminho, ",".join(r.middleware), r.controller, r.origem,
                                 _limpa_erro(r.erro)]))
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(("\n".join(linhas) + "\n").encode("utf-8"))


def contagem(rotas: list[Rota]) -> dict[str, int]:
    return {o: sum(1 for r in rotas if r.origem == o) for o in ORIGENS}


def inventario(raiz: Path) -> list[Rota]:
    """Inventario completo (laravel + rest + silex); grava `casos/_inventario.tsv` e imprime
    a contagem por origem (entra no resumo.md como limite de cobertura)."""
    laravel, fonte = rotas_laravel()
    rotas = laravel + varre_silex(raiz)
    grava_tsv(rotas)
    c = contagem(rotas)
    quebradas = sum(1 for r in rotas if r.erro)
    print(f"fonte: {fonte}")
    print("inventario de rotas: " + ", ".join(f"{o}={c[o]}" for o in ORIGENS) + f", total={len(rotas)}"
          + f"; com controller quebrado na referencia={quebradas}")
    return sorted(rotas, key=_chave)


if __name__ == "__main__":
    inventario(Path(__file__).resolve().parents[2])
