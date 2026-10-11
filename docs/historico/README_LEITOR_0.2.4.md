> Atualização atual: **0.2.4**. Leia `LEIA_PRIMEIRO_v0_2_4.txt` e `docs/VALIDACAO_v0_2_4.md`. As instruções de versões abaixo são históricas quando divergirem.

# PDF Voz 0.2.3

Leitor desktop local para PDFs simples em português. Vozes Dora, Alex e Santa, reprodução por trechos, destaque no PDF, clique para iniciar, pausa/continuação, navegação, volume, velocidade e progresso salvo.

Para uma instalação nova, siga primeiro os requisitos e os passos de instalação em [README.md](README.md). As instruções abaixo são para quem já tem os modelos do teste anterior e quer instalar ou atualizar o leitor.

## Instalar ou atualizar o leitor

Extraia o conteúdo deste ZIP **na pasta do projeto anterior**, preservando `.venv` e `models`. O arquivo `leitor_pdf.py` deve ficar ao lado de `2_TESTAR_VOZ.bat`. O teste antigo continua disponível.

Execute, nesta ordem:

```powershell
.\4_ATUALIZAR_LEITOR.bat
.\5_ABRIR_LEITOR.bat
```

A primeira etapa requer internet para instalar PySide6, PyMuPDF e dependências fixadas em `requirements_leitor.txt`. Não baixa os modelos. A segunda abre a interface. Se a pasta `models` não estiver ao lado do aplicativo, uma janela permite selecionar a pasta do teste anterior. Os dois arquivos esperados são `kokoro-v1.0.onnx` e `voices-v1.0.bin`.

Alvo: Python 3.12 x64 / Windows 11. Não executar como administrador. Reserve cerca de 1 GB adicional como margem para a interface/dependências; o tamanho exato depende do ambiente. Se instalada em pasta separada, a atualização cria seu próprio `.venv`; ainda poderá usar a pasta de modelos anterior sem copiá-la.

No VS Code, abra a pasta original e selecione `.venv\Scripts\python.exe`. Execução direta:

```powershell
.\.venv\Scripts\python.exe leitor_pdf.py
```

## Fluidez da versão 0.2.3

O leitor pede o áudio sem o recorte automático de silêncio do Kokoro. Em seguida,
remove apenas silêncio externo com limiar conservador e margem de proteção para
sons fracos. Mantém cerca de 300 ms após frases, 180 ms após vírgula/ponto e vírgula/
dois-pontos, e ao menos 120 ms nos demais limites. A velocidade de reprodução afeta
essas durações. O interior do áudio não é recortado.

Mudanças de bloco do PDF não separam continuações evidentes (próxima palavra em
minúscula, exceto após dois-pontos, ou anterior terminada em vírgula/ponto e vírgula).
A regra é heurística, voltada a PDFs simples de uma coluna. O limite de 360 caracteres
permanece e ainda pode dividir frases longas. Não há correção automática de palavras
hifenizadas nem garantia de entonação perfeita.

Ao atualizar, retoma o início do trecho que contém o ponto anterior, pois a duração
do áudio mudou. Quando a divisão dos trechos muda, a posição é remapeada pela
contagem de palavras do mesmo PDF. Voz, páginas e controles são preservados.
CPU permanece com duas threads. Sem novas dependências ou modelos.

## Ajustes da versão 0.2.2

Removidos o texto duplicado acima dos controles e a barra de navegação do livro. O espaço liberado fica disponível para o PDF. A barra de reserva de áudio permanece.

## Como usar

1. Clique em **Abrir PDF**. A extração ocorre em um processo separado, com indicação de páginas processadas.
2. Vá a uma página de conteúdo. O número indicado é a página física do arquivo, começando em 1.
3. Clique na frase desejada no PDF ou na lista **Trechos**. Esse clique inicia a preparação e depois a reprodução. O botão Reproduzir começa pelo trecho selecionado ou salvo.
4. O destaque **amarelo** identifica o trecho selecionado/em preparação; **verde** identifica o trecho em reprodução.
5. Use Pausar/Continuar. Navegue pelas páginas, pelo sumário ou clicando no texto do PDF.
6. Os botões Página mudam apenas a página exibida. Trecho muda a posição de leitura. O sumário seleciona o primeiro trecho da página do capítulo e deixa a reprodução pausada.
7. Desative **Acompanhar leitura** para consultar outras páginas. Arrastar a página permite mover a visualização sem selecionar uma frase.
8. Em **Recentes**, dê dois cliques no livro para reabri-lo. O aplicativo recupera o ponto salvo e aguarda Reproduzir.

Atalhos: Ctrl+O abre arquivo; Espaço alterna reprodução/pausa; Page Up/Page Down navegam visualmente.

## Voz, saída e volume

Use **Saída de áudio** para escolher o fone ou alto-falante reconhecido pelo sistema. **Padrão do sistema** acompanha mudanças notificadas pelo Qt. **Atualizar saídas** força uma nova consulta. Se uma saída escolhida for desconectada, usa a padrão temporariamente e volta à escolhida quando ela reaparecer.

**Volume do leitor** controla apenas esta aplicação, de 0% a 100%. O botão **Som do Windows** abre as configurações do Windows; ali confira o dispositivo e o mixer durante a reprodução. O controle do leitor não representa nem altera o volume mestre do Windows. A seleção explícita de dispositivo foi implementada, mas o problema relatado com o volume do Windows ainda requer validação no equipamento real.

**Voz** oferece Dora, Alex e Santa em português, usando os modelos existentes. Mudar de voz reinicia a frase atual; um cálculo antigo em andamento pode precisar terminar antes de começar a nova voz. Não recarrega o modelo por essa troca. A preferência de voz é global; ao reabrir um livro salvo com outra voz, retoma o início da frase para evitar usar um deslocamento de tempo incompatível.

## Reserva de áudio e espera

- Reserva inicial: **15, 30 ou 60 segundos de áudio na velocidade selecionada** (padrão: 30), respeitando os limites dos trechos. Não é uma espera fixa de 60 segundos.
- **Ouvir o que já está pronto** permite iniciar com o trecho atual pronto sem completar a reserva. Só fica disponível durante a preparação com áudio utilizável.
- Reduzir a reserva diminui a quantidade a preparar antes de começar; não acelera a síntese. Pode aumentar as pausas durante a leitura.
- Geração continua enquanto escuta. No máximo cerca de **90 segundos à frente**, mais o trecho em geração. É um horizonte de preparação, não a geração antecipada do livro inteiro.
- Ao acabar a reserva, o leitor prepara novamente até a reserva selecionada e retoma automaticamente.
- Perto do fim do livro, começa assim que todo o conteúdo restante estiver pronto, mesmo que dure menos que a reserva selecionada.
- Ao clicar em um trecho já preparado, pode começar imediatamente. Se ainda não houver áudio, aplica-se a preparação inicial.
- Pausar impede novos pedidos de síntese; o pedido já em andamento pode terminar. Clicar em outro ponto invalida o resultado antigo. Esse cálculo nativo pode precisar terminar antes de o próximo começar, mantendo apenas uma geração por vez.
- O modelo fica carregado durante o livro. Fechar/trocar o livro encerra o processo e libera memória.

O RTF 1,24 medido no teste inicial não é uma promessa para esta versão. A síntese por sentença pode ter desempenho e entonação diferentes. Em velocidades maiores, a reserva se consome mais rápido. A interface mede a duração dos WAVs efetivamente prontos.

## Áudios temporários e progresso

Os áudios ficam numa única pasta interna por sessão. O menu **Arquivo → Abrir pasta de dados e diagnóstico** abre o local exato, criado em AppLocalData pelo Qt. No Windows normalmente fica abaixo de `%LOCALAPPDATA%\PDFVozLocal\PDFVoz`.

- `audio/session_*`: WAVs temporários. Mantém até dois trechos anteriores e a janela futura preparada.
- `leitura.sqlite3`: progresso, configuração, histórico e texto/coordenadas extraídos. Não contém o PDF original nem os áudios.
- `logs`: diagnóstico; o log principal tem rotação, limitado a aproximadamente 3 MB.

Os trechos antigos são descartados conforme a leitura avança. Fechar o livro, trocar de livro ou usar **Limpar áudios** interrompe a síntese e remove o áudio. Se o Windows ainda estiver liberando algum arquivo, o programa tenta novamente. A próxima abertura também limpa resíduos deixados por encerramento abrupto. Uma trava de instância evita dois leitores disputando a mesma pasta.

O teto adicional de proteção é **500 MiB** por sessão; atingir o teto interrompe a preparação com uma mensagem. A janela de 90 segundos normalmente fica muito abaixo desse teto. Não há exportação permanente nesta versão. Os WAVs criados pelo teste 0.1 na pasta `resultados` não pertencem ao cache do leitor e podem ser removidos manualmente quando não forem mais úteis.

Progresso salvo a cada cinco segundos e ao pausar, navegar ou fechar. Ao reabrir, o áudio é gerado novamente e a posição dentro do trecho é aplicada após o player permitir navegação temporal. Se o backend não permitir isso, retoma no início daquele trecho. O arquivo é identificado por SHA-256, permitindo reconhecer uma cópia idêntica e distinguir um PDF alterado.

## Correção de português e privacidade

A correção validada no teste 0.1.1 está incorporada: consulta os idiomas anunciados pelo eSpeak e preserva português brasileiro. Usa a biblioteca de pronúncia do pacote instalado. Quando o caminho do Windows tem acentos, pode manter **uma cópia reutilizável de dados públicos de pronúncia** em `%PUBLIC%\PDFVozPronuncia_0_2`, sem livros ou áudios. Essa pasta contém dependências reutilizadas entre execuções, não um novo conjunto a cada reprodução. Pode ser removida após fechar o aplicativo e será reconstruída se necessária.

O código desativa telemetria do ONNX Runtime antes da inicialização e pela API. A leitura não chama servidores, não envia PDFs e não exige chave de API. Instalação de dependências requer internet. PDFs protegidos solicitam senha e não a salvam no banco. Não são executados scripts nem abertos links do PDF.

## Limitações conhecidas

- Destinado a PDFs textuais de uma coluna. OCR, tabelas complexas e duas colunas não foram implementados.
- Extração conserva palavras/hífens e pode narrar cabeçalhos, notas, referências e elementos editoriais. Só números isolados nas margens são excluídos. Não há revisão automática do conteúdo.
- Uma frase longa pode ser dividida em trechos de até cerca de 360 caracteres. Abreviações comuns são protegidas, mas a segmentação não é perfeita. Há múltiplas regiões de destaque por trecho, com coordenadas canônicas e transformação para a página rotacionada.
- O player troca arquivos entre trechos: podem existir pequenas pausas. Não é prometida reprodução sem intervalos perceptíveis.
- O destaque é por trecho/sentença, não palavra por palavra. A precisão temporal depende dos eventos do backend Qt.
- Vozes selecionáveis: Dora, Alex e Santa. Trocar a voz descarta os áudios preparados e reinicia o trecho atual, preservando a intenção de reproduzir ou pausar. Velocidade 0,75–2× afeta reprodução, sem regenerar o áudio. Compensação de tonalidade depende do backend.
- A primeira abertura reextrai o texto para conferir o arquivo. A lista de recentes é básica, sem capas ou organização por pastas.
- Trocar de livro reinicia o mecanismo de voz; a posição anterior é preservada.
- PDF e modelo não são copiados para dentro do aplicativo. Se mover o PDF, selecione o novo caminho; se mover modelos, use o menu Arquivo.

## Teste de aceitação no seu computador

1. Abra A Startup Enxuta, vá à página física 15 e clique em uma frase.
2. Aguarde a reserva; confirme som, frase destacada e avanço automático.
3. Pause no meio da frase e continue. Depois clique em um trecho distante enquanto a voz prepara outro.
4. Mude de página visualmente e teste desativar Acompanhar leitura.
5. Feche e reabra o livro por Recentes. Confirme a posição salva.
6. Pelo menu de diagnóstico, confira se `audio` foi limpo depois de fechar o livro.

Se ocorrer falha, envie a captura e `logs/leitor.log` da pasta de diagnóstico. Para falha de instalação, use `logs/instalacao_leitor.txt` na pasta do projeto. Os logs podem incluir caminhos locais; revise antes de compartilhar.

## Desenvolvimento e testes

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
.\.venv\Scripts\python.exe -m tests.integration_smoke models
```

O segundo teste gera somente um PDF e frases sintéticas de teste, usa os modelos locais e remove os dados temporários. Leia `docs/VALIDACAO_v0_2_3.md` para o alcance da validação já feita.
