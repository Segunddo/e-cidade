#!/usr/bin/env python3
import base64
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
GENERATOR = Path(__file__).with_name("gera_pimaco.php")
EXPECTED_TEXT = {
    "pimaco-modelo01.pdf": ("BEM:", 12),
    "pimaco-modelo02.pdf": ("BEM:", 12),
    "pimaco-qrcode.pdf": ("PLACA", 6),
    "pimaco-qrcode-rotulo.pdf": ("PLACA", 6),
}


def fail(message):
    print(f"FALHOU: {message}", file=sys.stderr)
    return 1


def main():
    php = sys.argv[1] if len(sys.argv) > 1 else "php8.5"
    result = subprocess.run(
        [php, "-d", "error_reporting=-1", "-d", "display_errors=stderr", str(GENERATOR)],
        check=True,
        capture_output=True,
        text=True,
    )
    if result.stderr:
        return fail(f"PHP emitiu avisos ou deprecations:\n{result.stderr}")

    documents = {}
    for line in result.stdout.splitlines():
        item = json.loads(line)
        documents[item["nome"]] = base64.b64decode(item["b64"], validate=True)

    if set(documents) != set(EXPECTED_TEXT):
        return fail(f"arquivos emitidos inesperados: {sorted(documents)}")

    with tempfile.TemporaryDirectory(prefix="ecidade-pimaco-") as directory:
        for name, (needle, count) in EXPECTED_TEXT.items():
            path = Path(directory) / name
            path.write_bytes(documents[name])

            info = subprocess.run(
                ["pdfinfo", str(path)],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            pages = re.search(r"^Pages:\s+(\d+)$", info, re.MULTILINE)
            size = re.search(r"^Page size:\s+([\d.]+) x ([\d.]+) pts \(A4\)$", info, re.MULTILINE)
            if not pages or pages.group(1) != "1" or not size:
                return fail(f"{name}: pagina/folha diferente do esperado\n{info}")
            if abs(float(size.group(1)) - 595.28) > 0.02 or abs(float(size.group(2)) - 841.89) > 0.02:
                return fail(f"{name}: dimensoes A4 inesperadas\n{info}")

            text = subprocess.run(
                ["pdftotext", str(path), "-"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            if text.count(needle) != count:
                return fail(f"{name}: esperava {count} ocorrencias de {needle!r}, recebeu {text.count(needle)}")

            if name == "pimaco-modelo01.pdf" and "PREFEITURA MUNICIPAL DE EXEMPLO" not in text:
                return fail(f"{name}: texto institucional ausente")

            if name.startswith("pimaco-qrcode"):
                images = subprocess.run(
                    ["pdfimages", "-list", str(path)],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout
                dimensions = re.findall(r"^\s*1\s+\d+\s+image\s+(\d+)\s+(\d+)\s", images, re.MULTILINE)
                if len(dimensions) != 6:
                    return fail(f"{name}: esperava 6 QR Codes, encontrou {len(dimensions)}")

                widths_and_heights = [(int(width), int(height)) for width, height in dimensions]
                if name.endswith("rotulo.pdf") and not all(height > width for width, height in widths_and_heights):
                    return fail(f"{name}: os QR Codes com rotulo nao incluem a area do rotulo")
                if name.endswith("qrcode.pdf") and not all(width == height for width, height in widths_and_heights):
                    return fail(f"{name}: os QR Codes sem rotulo nao sao quadrados")

    print("OK: 4 PDFs; modelos Pimaco (12 etiquetas cada), QR com/sem rotulo; A4 e conteudo conferidos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
