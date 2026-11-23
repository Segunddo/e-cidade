"""Stub do PSP (Banco do Brasil PIX): responde como o banco, com respostas FIXAS, e registra o que a aplicacao
enviou (metodo, caminho, corpo; o cabecalho Authorization e o corpo de credenciais sao redigidos).

Rotas simuladas (sdk dbseller/sdk-api-pix-bb): POST /oauth/token e POST/PUT /arrecadacao-qrcodes[/...].
"""
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RESPOSTA_TOKEN = {"access_token": "stub-token", "token_type": "Bearer", "expires_in": 600}
RESPOSTA_QRCODE = {
    "timestampCriacaoSolicitacao": "2026-01-01T00:00:00.000Z", "estadoSolicitacao": "ATIVA",
    "codigoConciliacaoSolicitante": "STUB0001", "numeroVersaoSolicitacaoPagamento": 1,
    "linkQrCode": "pix.stub.invalid/qr/STUB0001", "qrCode": "00020126STUBQRCODE6304ABCD"}
_RE_SEGREDO = re.compile(r"(client_secret|password|senha|developer_application_key|gw-dev-app-key)=[^&\s]*", re.I)


class PixStub:
    def __init__(self, porta: int = 0):
        self.chamadas: list[dict] = []
        stub = self

        class H(BaseHTTPRequestHandler):
            def _atende(self):
                n = int(self.headers.get("Content-Length") or 0)
                corpo = self.rfile.read(n).decode("utf-8", errors="replace") if n else ""
                caminho = self.path.split("?")[0]
                stub.chamadas.append({"metodo": self.command, "caminho": caminho,
                                      "corpo": _RE_SEGREDO.sub(r"\1=<redigido>", corpo),
                                      "tem_autorizacao": "Authorization" in self.headers})
                resp = RESPOSTA_TOKEN if caminho.endswith("/oauth/token") else RESPOSTA_QRCODE
                dados = json.dumps(resp).encode()
                self.send_response(200 if caminho.endswith("/oauth/token") else 201)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(dados)))
                self.end_headers()
                self.wfile.write(dados)

            do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = _atende

            def log_message(self, *a):  # silencioso
                pass

        self._srv = ThreadingHTTPServer(("127.0.0.1", porta), H)
        self.porta = self._srv.server_address[1]
        self._th = threading.Thread(target=self._srv.serve_forever, daemon=True)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.porta}"

    def inicia(self) -> "PixStub":
        self._th.start()
        return self

    def para(self) -> None:
        self._srv.shutdown()
        self._srv.server_close()
        self._th.join(timeout=5)
