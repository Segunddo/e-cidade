# PIX e Pimaco: o que foi feito e o que falta

Este documento resume as provas feitas para executar PIX do Banco do Brasil e etiquetas Pimaco com PHP 8.5 e Laravel 13. Elas são **testes isolados**: ajudam a encontrar problemas sem trocar as dependências usadas hoje pelo restante do e-Cidade.
Não significam que o sistema completo já foi migrado, nem que está pronto para produção.

## Em poucas palavras

Foi montado um ambiente de teste separado, com versões novas das bibliotecas. Nele, foram
gerados PDFs reais usando o código de etiquetas do e-Cidade e simuladas as conversas do PIX
com o Banco do Brasil. Os testes passaram no PHP 8.5.12. Nenhum teste chamou o banco de verdade,
usou credenciais reais ou alterou o Composer compartilhado pela aplicação.

O exemplo é parecido com testar uma peça nova numa bancada antes de instalá-la na máquina:
mostra que aquela peça funciona no teste, mas ainda não prova que todo o sistema está pronto.

### Palavras que aparecem neste resumo

- **Composer:** ferramenta que escolhe e instala as bibliotecas do sistema.
- **SDK:** biblioteca pronta do Banco do Brasil, usada para pedir acesso e criar cobranças PIX.
- **OAuth:** etapa em que o sistema pede uma autorização temporária para conversar com o banco.
- **Homologação:** ambiente de testes do banco, separado de pagamentos reais.
- **Latin-1 e UTF-8:** duas formas de guardar letras acentuadas; o teste confere que a conversão
  entre elas mantém o nome correto.
- **TLS/certificado:** conferência de que a conexão está falando com o servidor verdadeiro do
  banco.

## O que foi feito, passo a passo

### 1. Criamos uma bancada separada

Cada prova tem seu próprio arquivo de dependências e sua própria pasta de bibliotecas:

- Pimaco: `ecidade/tests/sistema/documentos/`;
- PIX: `ecidade/tests/sistema/pix/`;
- bibliotecas instaladas para os testes: `runtime-85/pimaco-vendor/` e
  `runtime-85/pix-vendor/`.

Assim, o PHP 7.4 e as bibliotecas que o sistema usa hoje não foram substituídos. Os comandos
para repetir as provas também ficaram registrados nas pastas.

### 2. Pimaco: conferimos as etiquetas produzidas

O teste usa os dois modelos de etiqueta e o gerador PDF que a aplicação já usa. Ele cria quatro
arquivos:

1. modelo Pimaco 1, com 12 etiquetas;
2. modelo Pimaco 2, com 12 etiquetas;
3. etiquetas com QR Codes sem texto abaixo do código;
4. etiquetas com QR Codes com texto.

O verificador confere o tamanho A4, a quantidade de itens, textos e imagens. O texto do rótulo
do QR fica dentro da imagem; por isso, o teste confere a imagem, em vez de procurar o rótulo
como texto selecionável no PDF.

Também ajustamos a prova para detectar avisos do PHP 8.5 e corrigimos os campos que os builders
gravavam sem declarar. Para contornar incompatibilidades das bibliotecas antigas, foram
preparados pequenos ajustes que o script aplica **somente na cópia descartável** delas. Os
arquivos de imagem e os textos extraídos antes e depois desses ajustes ficaram iguais.

### 3. PIX: resolvemos o conflito só na bancada

A versão do SDK do Banco do Brasil travada hoje exige Guzzle 7.5.0. Laravel 13 exige uma versão
mais nova do Guzzle. Isso impede instalar os dois juntos com as regras originais.

Para testar sem alterar a aplicação compartilhada, a bancada usa o mesmo código do SDK, mas
com uma cópia local de seus dados de instalação que aceita Guzzle 7.8.2 ou mais novo. O Composer
escolheu Guzzle 7.16.5. Essa cópia local **não é um fork publicado** e ainda não pode ser usada
como dependência oficial do sistema.

O teste conversa com o SDK por respostas inventadas e controladas:

1. simula o pedido de acesso (OAuth) e confere endereço, método e autenticação;
2. simula o pedido de criação do QR Code e confere o endereço e os dados enviados;
3. confere se o SDK lê corretamente uma resposta de sucesso;
4. usa o adaptador real do Banco do Brasil para montar os dados do pedido, inclusive o nome
   acentuado armazenado em Latin-1;
5. confirma que o teste não emite avisos ou depreciações no fluxo coberto.

Também substituímos `utf8_encode()`, que é obsoleto no PHP 8.5, por uma conversão explícita de
Latin-1 para UTF-8 no adaptador do Banco do Brasil. O objetivo é manter o mesmo texto enviado.

### 4. Registramos os limites dos testes

As provas passaram em PHP 8.5.12 e com as bibliotecas do Laravel 13.43.0 isoladas. Não foi
feita chamada ao Banco do Brasil, nem foi usada uma base de dados real. O restante da aplicação
não foi iniciado com Laravel 13. A instalação das bibliotecas de teste ainda mostra avisos do
Composer 2.7.1 do ambiente; esses avisos são do próprio instalador, não dos fluxos PIX/Pimaco
executados.

## O que ainda falta para PIX e Pimaco

### PIX do Banco do Brasil

- **Criar e aprovar um fork de verdade do SDK**, hospedado num repositório controlado pela
  equipe, com versão e regras de instalação mantidas. Hoje a alteração das regras existe
  apenas na bancada.
- **Rever a verificação do certificado do servidor.** O código atual configura
  `verify => false`, o que desliga essa conferência. Não se deve fazer chamada real antes de
  decidir e validar a configuração segura de TLS/certificados.
- **Testar em ambiente de homologação do banco**, com credenciais próprias de teste: obter
  acesso e criar um PIX. Acrescentar consulta, cancelamento e outros passos se forem usados
  pelo e-Cidade.
- **Testar falhas e respostas inesperadas**: credencial inválida, indisponibilidade, demora,
  resposta incompleta e erro do banco. Confirmar também o que o usuário vê e o que fica
  gravado quando uma tentativa falha.
- **Testar a gravação no e-Cidade** numa base de teste, incluindo o vínculo entre cobrança,
  código de barras, QR e recibo. A prova atual só verifica a comunicação simulada e a montagem
  dos dados.
- **Comparar os dois ambientes suportados** — PHP 7.4 e PHP 8.5 — e confirmar que a mudança de
  codificação produz o mesmo texto nos dois.
- **Analisar Banrisul e Itaú separadamente.** Esta etapa cobriu somente o SDK do Banco do
  Brasil. Os outros adaptadores não foram atualizados nem testados aqui.

### Pimaco

- Repetir a comparação dos PDFs no PHP 7.4 e no PHP 8.5. Neste ambiente não havia PHP 7.4
  disponível para essa comparação.
- Testar os modelos e dados que os usuários realmente imprimem: textos longos, acentos,
  códigos de barras, QR, margens e alinhamento em impressoras representativas.
- Confirmar o comportamento dentro da aplicação completa, com as dependências Laravel que
  serão escolhidas. A prova atual chamou os builders e o gerador PDF reais, mas não iniciou o
  e-Cidade completo.
- Transformar os pequenos ajustes das bibliotecas em uma solução aprovada e reproduzível para
  a instalação oficial, em vez de depender só do script de teste.

## O que outras equipes podem adiantar

Estas atividades podem começar em paralelo, desde que usem ambiente de teste e não alterem o
Composer compartilhado sem aprovação:

| Quem pode ajudar | Trabalho útil agora | Resultado esperado |
|---|---|---|
| Responsáveis pelo PIX/Tributário | Listar os passos do PIX realmente usados, as telas que os iniciam e o que deve acontecer em sucesso e erro. | Roteiro de aceitação com dados fictícios e regras de negócio conferidas. |
| Equipe de infraestrutura/segurança | Preparar homologação isolada, certificados confiáveis e armazenamento seguro para credenciais de teste. | Ambiente pronto para testar o banco sem produção e sem desligar a verificação TLS. |
| Responsáveis por patrimônio | Separar exemplos anonimizados de etiquetas e impressoras/modelos usados. | Amostras para comparar visualmente os PDFs no PHP 7.4 e 8.5. |
| Equipe de dependências | Verificar quem pode manter o fork do SDK e os ajustes das bibliotecas, revisar licença, origem, atualizações e alertas de segurança. | Pacotes aprovados e publicados com versões reproduzíveis. |
| Equipe do Laravel | Inventariar o que ainda prende a aplicação ao Laravel antigo: login, permissões, rotas de API, telas, tarefas em segundo plano, agendamentos e sessões. | Lista de trabalho com responsáveis, ordem e testes para cada parte. |
| Equipe de testes e áreas de negócio | Escolher fluxos representativos de arrecadação, tributos, financeiro, patrimônio e demais áreas afetadas. | Casos de teste que protejam cálculos, documentos e registros importantes. |

Nenhuma equipe deve usar credenciais de produção, apontar os testes a um banco real ou fazer
alterações em massa antes de existir uma cópia restaurável e um plano de retorno.

## Caminho até a migração completa

Em ordem simples:

1. **Decidir e preparar:** aprovar a versão final do Laravel, o ambiente de homologação, os
   responsáveis e como voltar atrás se algo falhar.
2. **Resolver as bibliotecas:** publicar/aprovar o SDK PIX e as correções Pimaco; revisar
   também as outras dependências que não aceitam a versão nova.
3. **Atualizar a aplicação:** adaptar login e permissões, rotas, telas, tarefas, sessões,
   configurações e integrações ao Laravel escolhido.
4. **Testar com cada área:** rodar testes automáticos e confirmar com as equipes os fluxos
   importantes, usando cópia de banco e serviços de teste.
5. **Ensaiar a operação:** verificar arquivos, certificados, filas, tarefas agendadas, logs,
   backup e retorno à versão anterior.
6. **Homologar e só então implantar:** obter aprovação técnica e funcional, instalar de forma
   controlada e acompanhar os erros após a liberação.

**A migração só estará completa** quando o sistema inteiro — não apenas PIX e Pimaco isolados —
resolver suas dependências, iniciar no ambiente escolhido, passar pelos testes das áreas e for
aprovado em homologação com plano de retorno. O plano detalhado e as demais pendências estão em
[plano-de-migracao.md](./plano-de-migracao.md) e
[decisoes-pendentes.md](./decisoes-pendentes.md).
