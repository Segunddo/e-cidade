import hashlib
import re

# (motivo, padrao, marcador) -- sempre sobre bytes, nunca decodificar.
REGRAS: list[tuple[str, re.Pattern[bytes], bytes]] = [
    # Portado de scratchpad/cmp.py (NORM), na mesma ordem.
    # Id de sessao em links/formularios: muda a cada requisicao.
    ("sid de sessao", re.compile(rb"sid=[0-9a-f]{8,}"), b"sid=X"),
    # Parametro arquivo= em base64 (nome/caminho temporario codificado).
    ("arquivo base64", re.compile(rb"arquivo=[A-Za-z0-9+/=]{12,}"), b"arquivo=X"),
    # Nome de janela gerado com contador/timestamp (wname123...).
    ("wname", re.compile(rb"wname[0-9]+"), b"wnameX"),
    # Nome de iframe PHP gerado dinamicamente.
    ("iframe php", re.compile(rb"iframe[A-Za-z0-9]{4,}\.php"), b"iframeX.php"),
    # Hash MD5 (32 hex) usado como token/identificador por requisicao.
    ("md5", re.compile(rb"[0-9a-f]{32}"), b"MD5X"),
    # nomeArquivo=... carrega nome temporario de arquivo gerado.
    ("nomeArquivo", re.compile(rb"nomeArquivo[^\s\"']*"), b"nomeArquivoX"),
    # PDF temporario: o nome carrega PID e timestamp, aleatorios por requisicao.
    ("pdf temporario", re.compile(rb"tmp/[A-Za-z0-9_]+\.pdf"), b"tmp/X.pdf"),
    # CSV/TXT temporario com timestamp no nome (arquivo_infra_escola_1791906927.csv);
    # dentro de JSON a barra vem escapada (tmp\/...). Achado no edu2.
    ("csv/txt temporario", re.compile(rb"tmp\\?/[A-Za-z0-9_]+\.(?:csv|txt)"), b"tmp/X.arq"),
    # A pagina de erro monta URL absoluta a partir de HTTP_HOST (ver $DB_URL_ABS),
    # entao ela carrega a porta do runtime que a serviu. Diferenca por construcao.
    ("porta do runtime", re.compile(rb"localhost:80(80|85|86|87)"), b"localhost:PORT"),
    # Data de criacao gravada dentro do PDF pelo FPDF: muda se as duas
    # requisicoes cairem em segundos diferentes. Passou a aparecer depois que
    # tmp/ virou gravavel e os relatorios comecaram a ser gerados de fato.
    ("data do pdf", re.compile(rb"/(CreationDate|ModDate) ?\(D:[0-9]{14}[^)]*\)"), b"/DateX"),
    # PHP 8 trocou a capitalizacao da mensagem do warning ("failed to open stream" -> "Failed to open stream"):
    # o mesmo warning sai nos dois runtimes (achado em pes2_contracheque_banrisul002, 200x200 so por isto).
    ("caixa de 'failed to open stream'", re.compile(rb"[Ff]ailed to open stream"), b"failed to open stream"),
]


def normaliza(corpo: bytes, regras=REGRAS) -> bytes:
    for _motivo, padrao, marcador in regras:
        corpo = padrao.sub(marcador, corpo)
    return corpo


def hash_corpo(corpo: bytes, regras=REGRAS) -> str:
    return hashlib.sha256(normaliza(corpo, regras)).hexdigest()
