"""Lint incremental em Docker. Compara sintaxe com a base no mesmo PHP."""
import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile


def git(*args):
    return subprocess.run(['git', *args], check=True, capture_output=True).stdout


def select_files(raw):
    return [name for name in raw.decode('utf-8', errors='surrogateescape').split('\0')
            if name and name.lower().endswith('.php')]


def classify(current, previous):
    if current == 0:
        return 'PASSOU'
    return 'FALHA_NOS_DOIS' if previous not in (None, 0) else 'NOVA_FALHA'


def lint(content, image):
    # Arquivo fora da arvore original, sem iniciar a aplicacao ou seus includes.
    with tempfile.TemporaryDirectory(prefix='ecidade-lint-') as directory:
        source = Path(directory, 'arquivo.php')
        source.write_bytes(content)
        # TemporaryDirectory usa 0700 no Linux. Sem DAC_OVERRIDE, o root do
        # container nao atravessa a pasta do runner (outro UID).
        # Somente esta copia temporaria fica legivel; o mount continua readonly.
        Path(directory).chmod(0o755)
        source.chmod(0o644)
        result = subprocess.run([
            'docker', 'run', '--rm', '--network', 'none', '--read-only',
            '--cap-drop=ALL', '--security-opt=no-new-privileges',
            '--memory=256m', '--pids-limit=64',
            '--mount', f'type=bind,src={directory},dst=/lint,readonly',
            image, 'php', '-n', '-d', 'short_open_tag=1', '-l', '/lint/arquivo.php'
        ], stdin=subprocess.DEVNULL, capture_output=True, timeout=45)
    # PHP usa 255 para erro de sintaxe. Outros codigos indicam falha do ambiente.
    if result.returncode not in (0, 255):
        raise RuntimeError('Docker/PHP indisponivel: ' + result.stderr.decode('utf-8', errors='replace')[:1000])
    return result.returncode


def run(base, version):
    if not re.fullmatch(r'[a-fA-F0-9]{40}', base):
        raise ValueError('Informe o SHA completo da base do PR.')
    if version not in ('7.4', '8.5'):
        raise ValueError('PHP deve ser 7.4 ou 8.5.')
    head = git('rev-parse', 'HEAD').decode().strip()
    ancestor = git('merge-base', base, head).decode().strip()
    files = select_files(git('diff', '--name-only', '-z', '--no-renames',
                            '--diff-filter=ACM', ancestor, head, '--'))
    report = {'base_sha': base, 'merge_base': ancestor, 'head_sha': head,
              'php': version, 'files': [], 'errors': [],
              'scope': 'Sintaxe de arquivos PHP adicionados ou alterados; short_open_tag=1.'}
    for name in files:
        try:
            parts = PurePosixPath(name).parts
            if name.startswith('/') or '..' in parts:
                raise ValueError('Caminho fora da arvore do repositorio.')
            mode = git('ls-tree', head, '--', name).split(b' ', 1)[0]
            if mode not in (b'100644', b'100755'):
                raise ValueError('Entrada PHP nao e arquivo regular. Requer revisao.')
            current = lint(git('show', head + ':' + name), 'php:' + version + '-cli')
            previous = None
            if current:
                previous_entry = git('ls-tree', ancestor, '--', name)
                if previous_entry:
                    if previous_entry.split(b' ', 1)[0] not in (b'100644', b'100755'):
                        raise ValueError('Entrada anterior nao e arquivo PHP regular.')
                    previous = lint(git('show', ancestor + ':' + name), 'php:' + version + '-cli')
            report['files'].append({'path': name, 'status': classify(current, previous),
                                    'head_exit': current, 'base_exit': previous})
        except (subprocess.SubprocessError, OSError, ValueError, RuntimeError) as error:
            report['errors'].append({'path': name, 'error': str(error)})
            break
    report['status'] = ('ERRO_AMBIENTE' if report['errors'] else
                        'NOVA_FALHA' if any(row['status'] == 'NOVA_FALHA' for row in report['files']) else
                        'INCONCLUSIVO' if any(row['status'] == 'FALHA_NOS_DOIS' for row in report['files']) else
                        'SEM_PHP_ALTERADO' if not files else 'SEM_NOVA_FALHA')
    report['selected'] = len(files)
    report['checked'] = len(report['files'])
    return report


def markdown(report):
    labels = {'SEM_PHP_ALTERADO': 'Nenhum PHP alterado no lote',
              'SEM_NOVA_FALHA': 'Sintaxe aprovada nos arquivos selecionados',
              'NOVA_FALHA': 'Nova falha de sintaxe detectada',
              'INCONCLUSIVO': 'Falha na base e no lote: requer analise',
              'ERRO_AMBIENTE': 'Execucao incompleta por erro de ambiente'}
    lines = ['## Lint PHP ' + report.get('php', ''), '', labels[report['status']], '',
             'Selecionados: ' + str(report.get('selected', 0)) +
             '. Conferidos: ' + str(report.get('checked', 0)) + '.', '',
             'Esta verificacao cobre sintaxe isolada. Os fluxos funcionais seguem no catalogo de regressao.', '']
    for row in report.get('files', []):
        # Caminho arbitrario em Git e serializado como texto, sem HTML ou links ativos.
        name = json.dumps(row['path'], ensure_ascii=True).replace('<', '&lt;').replace('>', '&gt;').replace('`', '&#96;')
        lines.append('- ' + row['status'] + ' - `' + name + '`')
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True)
    parser.add_argument('--php', choices=['7.4', '8.5'], required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--summary')
    args = parser.parse_args()
    try:
        report = run(args.base, args.php)
    except (subprocess.SubprocessError, OSError, ValueError) as error:
        report = {'status': 'ERRO_AMBIENTE', 'errors': [str(error)]}
    destination = Path(args.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=True, indent=2) + '\n', encoding='ascii')
    destination.with_suffix('.md').write_text(markdown(report), encoding='utf-8')
    if args.summary:
        with open(args.summary, 'a', encoding='utf-8') as summary:
            summary.write(markdown(report))
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return exit_code(report['status'])


def exit_code(status):
    if status in ('ERRO_AMBIENTE', 'INCONCLUSIVO'):
        return 2
    return 1 if status == 'NOVA_FALHA' else 0


if __name__ == '__main__':
    raise SystemExit(main())
