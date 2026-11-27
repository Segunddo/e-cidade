"""Compara copias antes/depois. Evidencia dirigida, sem aceite funcional automatico."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def command(args):
    proc = subprocess.run(args, capture_output=True, timeout=90)
    return {'exit': proc.returncode, 'stdout': proc.stdout.decode('utf8', errors='replace'),
            'stderr': proc.stderr.decode('utf8', errors='replace')}


def compare(php74, php85, original, adjusted, out):
    original, adjusted, out = (Path(p).resolve() for p in (original, adjusted, out))
    if original == adjusted:
        raise ValueError('As copias original e ajustada precisam ser diferentes.')
    if any(out == p or p in out.parents for p in (original, adjusted)):
        raise ValueError('Guarde evidencias fora das arvores de codigo.')
    out.mkdir(parents=True, exist_ok=True)
    report = {'scope': 'Prova dirigida das bibliotecas; nao substitui MCP/regressao de telas',
              'acceptance': 'PENDENTE_DOCKER_MCP_E_TELAS', 'versions': {}, 'lint': [], 'runs': []}
    for version, executable in [('7.4', php74), ('8.5', php85)]:
        runtime = command([executable, '-n', '-r', 'echo PHP_VERSION;'])
        if runtime['exit'] or not runtime['stdout'].startswith(version+'.'):
            raise RuntimeError('Runtime inesperado: '+version)
        report['versions'][version] = runtime['stdout']
        for phase, root in [('original', original), ('ajustado', adjusted)]:
            for name in ['fpdf151/fpdf.php', 'libs/JSON.php']:
                result = command([executable, '-n', '-l', str(root/name)])
                expected_ok = phase == 'ajustado' or version == '7.4'
                if (result['exit'] == 0) != expected_ok:
                    raise RuntimeError('Sintaxe inesperada: '+phase+' '+version+' '+name)
                failure_text = result['stdout']+result['stderr']
                offset_failure = ('curly braces' in failure_text or
                                  'unexpected token "{"' in failure_text)
                if not expected_ok and not offset_failure:
                    raise RuntimeError('Original falhou por outra causa: '+name)
                report['lint'].append(dict(php=version, phase=phase, path=name, **result))
    test = Path(__file__).with_name('prova_offsets_nucleo.php')
    outputs = []
    for label, executable, root in [('original74', php74, original),
                                     ('ajustado74', php74, adjusted), ('ajustado85', php85, adjusted)]:
        pdf = out/(label+'.pdf')
        if pdf.exists():
            raise ValueError('Use uma pasta nova de evidencias: '+str(pdf))
        result = command([executable, '-n', str(test), str(root), str(pdf)])
        if result['exit'] or result['stderr']:
            raise RuntimeError('Prova falhou em '+label+': '+result['stdout']+result['stderr'])
        data = json.loads(result['stdout'])
        if data['cases'] != 557:
            raise RuntimeError('Contagem da prova inesperada.')
        actual_pdf_hash = hashlib.sha256(pdf.read_bytes()).hexdigest()
        if actual_pdf_hash != data['pdf_normalized_sha256']:
            raise RuntimeError('PDF gravado diverge do resultado da prova.')
        outputs.append(result['stdout'])
        report['runs'].append({'label': label, 'cases': data['cases'],
                              'json_sha256': hashlib.sha256(result['stdout'].encode()).hexdigest(),
                              'pdf_sha256': actual_pdf_hash})
        (out/(label+'.json')).write_text(result['stdout'], encoding='utf8')
    if not outputs[0] == outputs[1] == outputs[2]:
        raise RuntimeError('Diferenca entre referencia e ajuste. Nao publicar como aprovado.')
    report['identical'] = True
    report['normalization'] = 'Somente CreationDate do PDF, com o mesmo comprimento.'
    report['deprecations'] = 'E_DEPRECATED excluido dos casos dirigidos; avisos restantes no lint registrados.'
    (out/'relatorio.json').write_text(json.dumps(report, ensure_ascii=True, indent=2)+'\n', encoding='ascii')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['php74', 'php85', 'original', 'ajustado', 'out']:
        parser.add_argument('--'+name, required=True)
    args = parser.parse_args()
    try:
        compare(args.php74, args.php85, args.original, args.ajustado, args.out)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        parser.exit(1, str(error)+'\n')
    print('557 casos identicos em 3 rodadas e PDFs identicos. Aceite MCP/funcional pendente.')


if __name__ == '__main__':
    main()
