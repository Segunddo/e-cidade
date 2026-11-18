import unittest
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch
from lint_alterados import classify, exit_code, lint, markdown, run, select_files


class LintTests(unittest.TestCase):
    def test_selecao_preserva_espacos_e_ignora_outros_arquivos(self):
        self.assertEqual(select_files(b'ecidade/um arquivo.php\0README.md\0ecidade/X.PHP\0'),
                         ['ecidade/um arquivo.php', 'ecidade/X.PHP'])

    def test_classificacao_distingue_falhas_herdadas(self):
        self.assertEqual(classify(0, None), 'PASSOU')
        self.assertEqual(classify(255, 0), 'NOVA_FALHA')
        self.assertEqual(classify(255, None), 'NOVA_FALHA')
        self.assertEqual(classify(255, 255), 'FALHA_NOS_DOIS')

    def test_recusa_base_que_nao_e_sha(self):
        with self.assertRaises(ValueError):
            run('--qualquer-coisa', '7.4')

    @patch('lint_alterados.git', side_effect=[b'b' * 40, b'a' * 40, b'README.md\0'])
    @patch('lint_alterados.lint')
    def test_documentacao_nao_roda_php(self, lint, git):
        self.assertEqual(run('a' * 40, '8.5')['status'], 'SEM_PHP_ALTERADO')
        lint.assert_not_called()

    @patch('lint_alterados.git', side_effect=[b'b' * 40, b'a' * 40, b'ecidade/exemplo.php\0', b'100644 blob exemplo', b'<?php'])
    @patch('lint_alterados.lint', side_effect=RuntimeError('Docker indisponivel'))
    def test_erro_docker_nao_passa_como_falha_herdada(self, lint, git):
        result = run('a' * 40, '8.5')
        self.assertEqual(result['status'], 'ERRO_AMBIENTE')
        self.assertEqual(len(result['errors']), 1)

    @unittest.skipUnless(os.environ.get('ECIDADE_LINT_IMAGE'), 'Requer imagem PHP e Docker')
    def test_php_real_aceita_valido_e_recusa_erro_de_sintaxe(self):
        image = os.environ['ECIDADE_LINT_IMAGE']
        self.assertEqual(lint(b'<?php echo "exemplo";', image), 0)
        self.assertEqual(lint(b'<?php function {', image), 255)

    def test_classificacao_define_codigos_sem_aprovar_inconclusivo(self):
        self.assertEqual(exit_code('SEM_NOVA_FALHA'), 0)
        self.assertEqual(exit_code('SEM_PHP_ALTERADO'), 0)
        self.assertEqual(exit_code('NOVA_FALHA'), 1)
        self.assertEqual(exit_code('INCONCLUSIVO'), 2)
        self.assertEqual(exit_code('ERRO_AMBIENTE'), 2)

    def test_resumo_documental_diz_que_nenhum_php_foi_verificado(self):
        result = markdown({'status': 'SEM_PHP_ALTERADO', 'selected': 0, 'checked': 0})
        self.assertIn('Nenhum PHP alterado', result)
        self.assertIn('Conferidos: 0', result)

    @patch('lint_alterados.subprocess.run')
    def test_docker_recebe_bytes_originais_sem_rede_ou_execucao_do_script(self, runner):
        content = b'<?php /* acento latin1: \xe7 */'
        def fake_command(command, **kwargs):
            mount = command[command.index('--mount') + 1]
            directory = mount.split('src=', 1)[1].split(',dst=', 1)[0]
            self.assertEqual(Path(directory, 'arquivo.php').read_bytes(), content)
            self.assertIn('--read-only', command)
            self.assertEqual(command[command.index('--network') + 1], 'none')
            self.assertIn('-l', command)
            self.assertEqual(kwargs['stdin'], subprocess.DEVNULL)
            return Mock(returncode=0, stderr=b'')
        runner.side_effect = fake_command
        self.assertEqual(lint(content, 'php:7.4-cli'), 0)

    @patch('lint_alterados.Path.chmod', autospec=True)
    @patch('lint_alterados.subprocess.run')
    def test_permissoes_da_copia_temporaria_antes_do_container(self, runner, chmod):
        def check_command(command, **kwargs):
            mount = command[command.index('--mount') + 1]
            directory = Path(mount.split('src=', 1)[1].split(',dst=', 1)[0])
            self.assertEqual([call.args for call in chmod.call_args_list],
                             [(directory, 0o755), (directory / 'arquivo.php', 0o644)])
            self.assertIn('--cap-drop=ALL', command)
            self.assertTrue(mount.endswith(',readonly'))
            return Mock(returncode=0, stderr=b'')
        runner.side_effect = check_command
        self.assertEqual(lint(b'<?php echo 1;', 'php:7.4-cli'), 0)

    @patch('lint_alterados.subprocess.run', return_value=Mock(returncode=125, stderr=b'erro docker'))
    def test_erro_do_docker_e_erro_de_ambiente(self, runner):
        with self.assertRaises(RuntimeError):
            lint(b'<?php', 'php:8.5-cli')

    @patch('lint_alterados.subprocess.run', side_effect=subprocess.TimeoutExpired('docker', 45))
    def test_timeout_nao_passa_como_resultado_de_sintaxe(self, runner):
        with self.assertRaises(subprocess.TimeoutExpired):
            lint(b'<?php', 'php:8.5-cli')

    def test_diff_real_git_seleciona_renome_e_ignora_exclusao(self):
        # Git real num repositorio temporario; somente PHP/Docker sao simulados.
        with tempfile.TemporaryDirectory(prefix='ecidade-git-test-') as directory:
            def command(*args):
                return subprocess.run(['git', '-C', directory, *args], check=True,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
            command('init')
            command('config', 'user.name', 'Teste sintetico')
            command('config', 'user.email', 'teste@example.invalid')
            Path(directory, 'antes.php').write_bytes(b'<?php echo 1;')
            Path(directory, 'remover.php').write_bytes(b'<?php echo 2;')
            command('add', 'antes.php', 'remover.php')
            command('commit', '-m', 'Base sintetica')
            base = command('rev-parse', 'HEAD').decode().strip()
            command('mv', 'antes.php', 'nome com espaco.php')
            command('rm', 'remover.php')
            command('commit', '-m', 'Lote sintetico')
            import lint_alterados
            def git_here(*args):
                return command(*args)
            with patch.object(lint_alterados, 'git', side_effect=git_here), patch.object(lint_alterados, 'lint', return_value=0):
                result = run(base, '8.5')
            self.assertEqual(result['status'], 'SEM_NOVA_FALHA')
            self.assertEqual([row['path'] for row in result['files']], ['nome com espaco.php'])

    def test_fluxo_completo_classifica_erro_novo_e_falha_nos_dois(self):
        for previous_exit, expected in [(0, 'NOVA_FALHA'), (255, 'INCONCLUSIVO')]:
            outputs = [b'b' * 40, b'a' * 40, b'x.php\0', b'100644 blob atual',
                       b'<?php function {', b'100644 blob anterior', b'<?php anterior']
            with patch('lint_alterados.git', side_effect=outputs), patch('lint_alterados.lint', side_effect=[255, previous_exit]):
                result = run('a' * 40, '8.5')
            self.assertEqual(result['status'], expected)

    @patch('lint_alterados.git', side_effect=[b'b' * 40, b'a' * 40, b'link.php\0', b'120000 blob link'])
    @patch('lint_alterados.lint')
    def test_link_simbolico_exige_revisao(self, lint_mock, git_mock):
        self.assertEqual(run('a' * 40, '8.5')['status'], 'ERRO_AMBIENTE')
        lint_mock.assert_not_called()


if __name__ == '__main__':
    unittest.main()
