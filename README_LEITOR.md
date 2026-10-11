# Guia do leitor — PDF Voz 0.2.7

Instale pelo `INSTALAR.bat` e abra pelo `ABRIR.bat`. As instruções completas estão no [README](README.md).

## Interface

Use Painel lateral (Ctrl+B) para recolher ou mostrar Trechos, Sumário e Recentes. A divisória permite ajustar a largura; a preferência de visibilidade é salva. Abrir PDF e Configurações ficam no topo, junto do título. Página, zoom e Acompanhar leitura ficam na linha seguinte.

Trecho anterior, Reproduzir/Pausar, próximo trecho, velocidade e volume ficam sempre na barra inferior. A faixa fina indica a reserva de áudio, acompanhada de segundos prontos. Ouvir o que já está pronto continua na janela principal e só fica habilitado quando aplicável.

Configurações abre uma janela não modal: a reprodução continua enquanto você consulta as opções. Ela reúne voz, saída, reserva, tratamento da leitura, atualização de dispositivos, Som do Windows e Limpar áudios. As opções são aplicadas imediatamente; trocar voz ou tratamento continua regenerando os trechos como antes. Fechar configurações apenas fecha essa janela. Fechar livro fica no menu Arquivo.

## Leitura

Abra um PDF textual e use Reproduzir ou clique no trecho desejado. A interface oferece páginas, sumário, lista de trechos, zoom e acompanhamento automático. O destaque é por trecho, não por palavra. As vozes disponíveis são Dora, Alex e Santa. Volume e saída de áudio são controles do aplicativo; o botão Som do Windows abre os controles do sistema.

O processamento utiliza CPU com quatro threads de inferência. PDF e voz trabalham em processos separados da interface. O controle de velocidade ajusta a reprodução entre 0,75 e 2 vezes; não altera a velocidade de síntese do modelo.

## Pausa e reserva

A reserva inicial pode ser de 15, 30 ou 60 segundos de fala na velocidade selecionada. O comando Ouvir o que já está pronto permite iniciar antes de completar essa reserva. A geração prepara até aproximadamente 90 segundos à frente, mais o trecho em geração.

Depois que o mecanismo de voz foi iniciado, pausar interrompe a reprodução, mas permite continuar a preparação até esse limite. Apenas abrir o livro não carrega obrigatoriamente o modelo. Fechar ou trocar o livro encerra o processo de voz. Trocar a voz ou o modo de leitura descarta os áudios preparados para regenerá-los.

## Livros técnicos

Tratamento da leitura oferece Automático, Prosa e Código. O modo automático usa heurísticas do PDF e pode errar; escolha manualmente quando necessário. A preparação da fala trata números, símbolos e alguns termos, mantendo separado o texto usado para exibição. Não executa código extraído do livro. Não há OCR nem garantia de ordem correta em tabelas ou PDFs com várias colunas.

## Histórico e arquivos

O progresso é salvo periodicamente e ao pausar, navegar ou fechar. O menu Arquivo abre a pasta de dados, normalmente abaixo de `%LOCALAPPDATA%\PDFVozLocal\PDFVoz` no Windows. Ela contém `leitura.sqlite3`, logs e áudio temporário por sessão. Não apague o banco se quiser preservar o histórico.

O cache é limitado e limpo pelo leitor. O teto adicional por sessão é 500 MiB. Áudios do teste antigo em `resultados` são independentes e podem ser removidos quando não forem mais úteis. Remover livro atual do histórico exclui seu registro no aplicativo, sem apagar o PDF original.

A instalação e os modelos permanecem na pasta do projeto. Não mova ou exclua `.venv` ou `models` durante o uso. O programa não envia PDFs para serviços externos; a instalação usa internet para obter bibliotecas e modelos.

## Diagnóstico

Use Arquivo → Gerar diagnóstico atual, ou `ferramentas/DIAGNOSTICO.bat` se a janela não abrir. O diagnóstico permite conferir versão, dependências e processamento por CPU. Detalhes de erros ficam nos logs; revise caminhos locais antes de compartilhá-los.

Guias anteriores estão em `docs/historico` apenas como registro de evolução. Para o funcionamento atual, use este guia.

## Pausas e números na versão 0.2.7

Em modo Automático, o tipo extraído do trecho e do próximo trecho orienta a pausa: 550 ms ao entrar/sair de título, 420 ms entre prosa e código e pelo menos 280 ms ao encerrar uma linha de código. O ponto final em prosa mantém 300 ms; dois-pontos passam a 280 ms. São margens após o último som detectado, antes da aplicação da velocidade do player, e não tempos exatos entre palavras. O recorte conservador da fala foi mantido.

Os modos Prosa e Código forçam também a classificação usada para as pausas. Se a classificação automática errar, a pausa pode não corresponder à estrutura real do livro.

Em código, 000 é narrado como zero zero zero. Expressões com duas ou mais vírgulas entre grupos numéricos, como 1,000,000, têm a grafia explicitada também em prosa; decimais simples como 1,50 mantêm o tratamento anterior. Essa regra é conservadora para livros técnicos e não converte automaticamente essas expressões em milhões.
