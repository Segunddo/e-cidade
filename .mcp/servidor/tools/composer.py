"""analisar_composer: le composer.json/.lock (so leitura) e aponta o que trava a ida para PHP 8.5/Laravel 13.

Estrategia do grupo: o 7.4 fica INTACTO com o Laravel 8 do PR; o 8.5 ganha um composer proprio (Laravel 13 +
Passport 13). composer.json, composer.lock e vendor/ sao do grupo Laravel (regra 6 do CONTRIBUINDO.md).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from servidor.config import Config
from servidor.seguranca import ErroFerramenta, decodificar, relativo, resolver_caminho

ALVO_PHP = (8, 5, 0)

# Medido pelo grupo (guia 7.4 -> 8.5, 18/11/2026, Composer com PHP 8.5.12): com o Laravel novo e as versoes
# liberadas sobram 2 bloqueios, cada um com solucao ja medida.
BLOQUEIOS_CONHECIDOS: dict[str, str] = {
    "dbseller/sdk-api-pix-bb": "2.0.0 exige o Guzzle 7.5.0 exato. Solucao medida: ajuste minimo aplicado na "
                               "instalacao, so no 8.5, com prova contra duble de que os pedidos saem identicos.",
    "proner/phppimaco": "1.4.5 puxa endroid/qr-code ^2.5 e bacon-qr-code 1.0.3. Solucao medida: mantem a etiqueta "
                        "com o mesmo tamanho impresso.",
}

# pacote -> (problema, sugestao). Conhecimento curado; confirme no UPGRADE de cada pacote antes de subir.
ALERTAS: dict[str, tuple[str, str]] = {
    "laravel/framework": ("Laravel 8 nao roda oficialmente no PHP 8.5 (so 12 e 13 tem suporte); o alvo do grupo e "
                          "Laravel 13 (exige PHP >= 8.3)",
                          "^13.0 num composer SO do 8.5; o 7.4 fica com o Laravel 8 do PR (os degraus 9-11 nao tem "
                          "suporte no 8.5)"),
    "laravel/passport": ("Passport 10 acompanha Laravel 8/9; o 11 removeu Passport::routes()",
                         "^13 (alvo do grupo): enablePasswordGrant(), OAuthenticatable no model de usuario, "
                         "Passport::ignoreRoutes(), ids inteiros dos clientes sobre as tabelas oauth_* de hoje"),
    "laravel/tinker": ("versao antiga", "versao compativel com Laravel 13"),
    "fzaninotto/faker": ("pacote ABANDONADO (2020); exclui o PHP 8.5", "trocar por fakerphp/faker"),
    "phpunit/phpunit": ("PHPUnit 8 nao e suportado pelo Laravel 13",
                        "versao suportada pelo Laravel 13: setUp(): void, anotacoes viram atributos"),
    "mockery/mockery": ("versao fixa antiga (1.3.0)", "^1.6"),
    "doctrine/dbal": ("DBAL 2 sem suporte; o Laravel 11+ nao usa mais DBAL no Schema",
                      "remova se so servia ao ->change() de migrations; se o codigo usa DBAL direto, ^3.x/^4.x"),
    "lcobucci/jwt": ("3.4 e linha antiga (EOL)",
                     "versoes novas do Passport/league/oauth2-server pedem lcobucci/jwt mais novo; deixe o composer resolver"),
    "guzzlehttp/guzzle": ("versao fixa (7.5.0)", "^7.9 (depreciacoes do PHP 8.4 corrigidas); solte a fixacao exata"),
    "jeremeamia/superclosure": ("pacote ABANDONADO; serializa closures com APIs internas antigas",
                                "laravel/serializable-closure (ou opis/closure)"),
    "symfony/polyfill-php56": ("polyfill inutil em PHP 8", "remova"),
    "symfony/polyfill-php70": ("polyfill inutil em PHP 8", "remova"),
    "symfony/console": ("fixado em 5.x; o Laravel 13 traz Symfony bem mais novo", "solte a fixacao"),
    "symfony/process": ("fixado em 5.x; o Laravel 13 traz Symfony bem mais novo", "solte a fixacao"),
    "dbseller/sdk-api-pix-bb": ("BLOQUEIO medido: " + BLOQUEIOS_CONHECIDOS["dbseller/sdk-api-pix-bb"],
                                "siga a solucao do grupo Laravel; nao troque o pacote por conta propria"),
    "proner/phppimaco": ("BLOQUEIO medido: " + BLOQUEIOS_CONHECIDOS["proner/phppimaco"],
                         "siga a solucao do grupo Laravel; confira a etiqueta impressa contra o 7.4"),
    "symfony/filesystem": ("fixado em 5.x", "^7.0"),
    "symfony/yaml": ("fixado em 5.x", "^7.0"),
    "dompdf/dompdf": ("0.8 e antigo (falhas de seguranca conhecidas, PHP 8 parcial)", "^3.0 (confira a saida dos PDFs)"),
    "phpoffice/phpword": ("0.18 e antigo", "^1.x"),
    "phpoffice/phpspreadsheet": ("1.x antigo", "^1.29 ou ^2/^3 (PHP 8.x)"),
    "league/fractal": ("0.11 e muito antigo", "^0.20"),
    "barryvdh/laravel-ide-helper": ("2.x e para Laravel <= 9", "^3.x"),
    "fideloper/proxy": ("embutido no Laravel 9 (TrustProxies)", "remova e use Illuminate\\Http\\Middleware\\TrustProxies"),
    "fruitcake/laravel-cors": ("embutido no Laravel 9.2+", "remova e use Illuminate\\Http\\Middleware\\HandleCors"),
    "swiftmailer/swiftmailer": ("Laravel 9 trocou SwiftMailer por Symfony Mailer", "remova; ajuste customizacoes de Mail"),
    "zendframework/zend-eventmanager": ("Zend Framework ABANDONADO (virou Laminas)", "laminas/laminas-eventmanager"),
    "aferrandini/phpqrcode": ("pacote sem manutencao", "chillerlan/php-qrcode ou endroid/qr-code"),
    "intervention/image": ("v2 em modo de manutencao; v3 muda a API", "mantenha ^2.7 ate migrar as chamadas; depois ^3"),
    "mpdf/mpdf": ("confira versao minima para PHP 8.5", "^8.2"),
    "phpstan/phpstan": ("PHPStan 1.x nao entende tudo do PHP 8.4/8.5", "^2.x"),
    "squizlabs/php_codesniffer": ("tokens novos do PHP 8.x", "^3.10"),
}
PREFIXOS_INTERNOS = ("dbseller/",)


# ---------- restricoes do composer (subconjunto suficiente para `php`) ----------

def _partes(v: str) -> list[str]:
    v = v.strip().lstrip("vV")
    v = re.sub(r"[-@+].*$", "", v)
    partes = v.split(".")
    if not v or not all(p.isdigit() or p in ("*", "x", "X") for p in partes):
        raise ValueError(v)
    return partes


def _t(nums: list[int]) -> tuple[int, int, int]:
    nums = (nums + [0, 0, 0])[:3]
    return (nums[0], nums[1], nums[2])


def _limites(token: str) -> list[tuple[str, tuple[int, int, int]]]:
    if token in ("*", "x"):
        return []
    m = re.match(r"^(\^|~|>=|<=|>|<|!=|==|=)?(.+)$", token)
    if not m:
        raise ValueError(token)
    op, ver = m.group(1) or "", m.group(2)
    partes = _partes(ver)
    if any(p in ("*", "x", "X") for p in partes):
        base = [int(p) for p in partes[: next(i for i, p in enumerate(partes) if p in ("*", "x", "X"))]]
        if not base:
            return []
        return [(">=", _t(base)), ("<", _t(base[:-1] + [base[-1] + 1]))]
    nums = [int(p) for p in partes]
    v = _t(nums)
    if op == "^":
        if nums[0] > 0:
            return [(">=", v), ("<", (nums[0] + 1, 0, 0))]
        return [(">=", v), ("<", (0, v[1] + 1, 0))]
    if op == "~":
        if len(nums) <= 2:
            return [(">=", v), ("<", (nums[0] + 1, 0, 0))]
        return [(">=", v), ("<", (nums[0], nums[1] + 1, 0))]
    if op in ("", "=", "=="):
        return [(">=", v), ("<=", v)]
    return [(op, v)]


_OPS = {">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b, ">": lambda a, b: a > b, "<": lambda a, b: a < b,
        "!=": lambda a, b: a != b}


def aceita_versao(restricao: str, versao: tuple[int, int, int]) -> bool | None:
    """A restricao do composer aceita `versao`? None se nao der para interpretar."""
    try:
        for alt in re.split(r"\s*\|\|?\s*", restricao.strip()):
            alt = re.sub(r"(>=|<=|>|<|!=|==|=|\^|~)\s+", r"\1", alt)
            hifen = re.match(r"^(\S+)\s+-\s+(\S+)$", alt)
            if hifen:
                limites = [(">=", _t([int(p) for p in _partes(hifen.group(1))])),
                           ("<=", _t([int(p) for p in _partes(hifen.group(2))]))]
            else:
                limites = [x for tok in re.split(r"\s*,\s*|\s+", alt) if tok for x in _limites(tok)]
            if all(_OPS[op](versao, v) for op, v in limites):
                return True
        return False
    except (ValueError, StopIteration):
        return None


# ---------- tool ----------

def _ler_json(p: Path, rel: str) -> dict[str, Any]:
    try:
        return json.loads(decodificar(p.read_bytes()))
    except json.JSONDecodeError as e:
        raise ErroFerramenta("json_invalido", f"{rel} nao e JSON valido: {e}") from None


def analisar_composer(config: Config, caminho: str = "ecidade/composer.json") -> dict[str, Any]:
    arq = resolver_caminho(config.raiz, caminho, tipo="arquivo")
    if arq.name != "composer.json":
        raise ErroFerramenta("parametro_invalido", "informe o caminho de um composer.json")
    rel = relativo(config.raiz, arq)
    dados = _ler_json(arq, rel)
    req: dict[str, str] = dados.get("require", {}) or {}
    dev: dict[str, str] = dados.get("require-dev", {}) or {}

    lock_arq = arq.with_name("composer.lock")
    lock = _ler_json(lock_arq, relativo(config.raiz, lock_arq)) if lock_arq.is_file() else None
    instalados: dict[str, str] = {}
    lock_info = None
    avisos: list[str] = []
    if lock is not None:
        pacotes = [*(lock.get("packages") or []), *(lock.get("packages-dev") or [])]
        fora, sem, ilegivel = [], 0, []
        for p in pacotes:
            instalados[p["name"]] = p.get("version", "")
            r = (p.get("require") or {}).get("php")
            if not r:
                sem += 1
                continue
            ok = aceita_versao(r, ALVO_PHP)
            if ok is False:
                fora.append({"nome": p["name"], "versao": p.get("version", ""), "requer_php": r})
            elif ok is None:
                ilegivel.append({"nome": p["name"], "requer_php": r})
        lock_info = {
            "total_pacotes": len(pacotes),
            "php_85_fora_da_restricao": sorted(fora, key=lambda x: x["nome"]),
            "restricao_nao_interpretada": ilegivel,
            "sem_restricao_php": sem,
            "nota": "restricao que aceita 8.5 nao garante que o pacote funcione no 8.5 (muitos declaram ^8.0 sem testar)",
        }
    else:
        avisos.append("composer.lock nao encontrado: so as restricoes do composer.json foram analisadas")

    alertas = []
    for secao, mapa in (("require", req), ("require-dev", dev)):
        for nome, restr in sorted(mapa.items()):
            if nome == "php" or nome.startswith("ext-"):
                continue
            item = {"nome": nome, "secao": secao, "restricao": restr, "instalado": instalados.get(nome)}
            if nome in ALERTAS:
                item["problema"], item["sugestao"] = ALERTAS[nome]
                alertas.append(item)
            elif nome.startswith(PREFIXOS_INTERNOS):
                item["problema"] = "pacote interno"
                item["sugestao"] = "confira a compatibilidade com PHP 8.5/Laravel 13 no repositorio do pacote"
                alertas.append(item)

    php_req = req.get("php")
    presentes = set(req) | set(dev) | set(instalados)
    return {
        "dono": "composer.json, composer.lock e vendor/ sao do grupo Laravel: ninguem mexe sem combinar "
                "(CONTRIBUINDO.md, regra 6). O 7.4 fica com o Laravel 8 do PR; o 8.5 tera composer proprio.",
        "bloqueios_conhecidos": [{"nome": n, "situacao": s} for n, s in BLOQUEIOS_CONHECIDOS.items() if n in presentes],
        "arquivo": rel,
        "php_requerido": php_req,
        "php_requerido_aceita_85": aceita_versao(php_req, ALVO_PHP) if php_req else None,
        "laravel_framework": ({"restricao": req["laravel/framework"], "instalado": instalados.get("laravel/framework")}
                              if "laravel/framework" in req else None),
        "extensoes": sorted(k for k in req if k.startswith("ext-")),
        "alertas": alertas,
        "lock": lock_info,
        "avisos": avisos,
        "proximo_passo": "valide cada troca de pacote com rodar_regressao (bateria php e laravel) antes de commitar",
    }
