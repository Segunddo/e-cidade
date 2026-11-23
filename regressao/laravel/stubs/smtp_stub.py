"""SMTP de teste: aceita qualquer remetente/destinatario e GUARDA as mensagens (bytes) em `mensagens`.
Sem dependencias (smtpd saiu do Python 3.12): protocolo minimo HELO/EHLO, MAIL, RCPT, DATA, RSET, NOOP, QUIT."""
import socketserver
import threading


class SmtpStub:
    def __init__(self, porta: int = 0):
        self.mensagens: list[dict] = []   # {"de": str, "para": [str], "dados": bytes}
        stub = self

        class H(socketserver.StreamRequestHandler):
            def _r(self, linha: str):
                self.wfile.write((linha + "\r\n").encode())

            def handle(self):
                self._r("220 stub ESMTP")
                de, para = "", []
                while True:
                    linha = self.rfile.readline()
                    if not linha:
                        return
                    cmd = linha.decode("utf-8", "replace").strip()
                    up = cmd.upper()
                    if up.startswith(("EHLO", "HELO")):
                        self._r("250 stub")
                    elif up.startswith("MAIL FROM"):
                        de, para = cmd.split(":", 1)[1].strip().strip("<>").split(">")[0], []
                        self._r("250 ok")
                    elif up.startswith("RCPT TO"):
                        para.append(cmd.split(":", 1)[1].strip().strip("<>").split(">")[0])
                        self._r("250 ok")
                    elif up == "DATA":
                        self._r("354 end com <CRLF>.<CRLF>")
                        dados = []
                        while True:
                            l = self.rfile.readline()
                            if l in (b".\r\n", b".\n", b""):
                                break
                            dados.append(l[1:] if l.startswith(b"..") else l)
                        stub.mensagens.append({"de": de, "para": list(para), "dados": b"".join(dados)})
                        self._r("250 ok: queued")
                    elif up == "RSET":
                        de, para = "", []
                        self._r("250 ok")
                    elif up == "NOOP":
                        self._r("250 ok")
                    elif up == "QUIT":
                        self._r("221 bye")
                        return
                    else:
                        self._r("502 comando nao implementado")

        class S(socketserver.ThreadingTCPServer):
            allow_reuse_address = True
            daemon_threads = True

        self._srv = S(("127.0.0.1", porta), H)
        self.porta = self._srv.server_address[1]
        self._th = threading.Thread(target=self._srv.serve_forever, daemon=True)

    def inicia(self) -> "SmtpStub":
        self._th.start()
        return self

    def para(self) -> None:
        self._srv.shutdown()
        self._srv.server_close()
        self._th.join(timeout=5)
