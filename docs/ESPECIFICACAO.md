# Contrato inicial e continuidade do projeto

## Objetivo
Leitor desktop local de PDFs simples em português, com voz sob demanda, destaque por sentença, clique para narrar, pausa, velocidade e retomada. Windows x64. Sem contas ou APIs pagas no fluxo central.

## Etapa entregue
Etapa A: terminal de teste em CPU. Arquivos: app.py coordena; reader/assets.py prepara modelos; reader/engine.py sintetiza; reader/text.py prepara amostras; bootstrap.py instala. Sem GUI provisória para descartar depois. O WAV usa o player padrão do Windows.

## Decisões
- CPUExecutionProvider explícito, duas threads intra-op e uma inter-op. Uma instância do modelo por execução.
- Português configurado via lang='pt-br' na API do kokoro-onnx 0.6.1. Esta versão carrega a dependência eSpeak local; não exige Misaki para esta rota de teste.
- Modelo de precisão padrão como referência inicial. Quantização é hipótese futura a medir se RAM ou velocidade forem insuficientes.
- Sem sobrescrever livros. Um par WAV/JSON novo por teste.
- Python 3.12 x64 como alvo reproduzível. Dependências principais e transitivas fixadas a partir da resolução de pacotes para Windows/Python 3.12; versões instaladas também são registradas pelo instalador.

## Critérios para avançar
1. Instalação termina no Windows do usuário.
2. Dora ou Alex entrega voz confortável em trechos reais e acentos/números verificáveis.
3. Duas execuções consecutivas geram WAV válido sem falha.
4. RTF medido permite decidir prefetch e velocidade suportada. RTF >=1 não encerra a viabilidade: exige pré-geração ou ajuste do motor.
5. Uma nova amostra pode ser sintetizada sem internet após preparação.

## Contrato do futuro leitor
- Segmento persistente com ID, ordem lógica, texto original e normalizado.
- Regiões visuais em tabela separada: múltiplas regiões e páginas por segmento.
- Coordenadas de extração canônicas explicitadas; transformações de rotação, crop e zoom no visualizador.
- Progresso vinculado ao segmento e à identidade do áudio (voz/modelo/parâmetros). Mudança de voz invalida offset temporal antigo.
- Renderização e extração PyMuPDF fora da interface, sem chamadas concorrentes via threads.
- QMediaPlayer controlado na thread Qt responsável. Restaurar offset somente após mídia estar pronta e permitir seek.
- Identificador de geração/sessão impede resultado antigo de tomar o player.
- Prefetch limitado por memória e segundos de áudio; cancelamento lógico ao navegar.
- Clique numa sentença inicia narração dali; navegar visualmente por páginas não muda sozinho a narração.
- Áudio gerado em blocos maiores só poderá destacar sentenças com limites temporais válidos.

## Fora do MVP
OCR, duas colunas complexas, chat, LLM, resumo, nuvem, marcação por palavra, exportação de livro completo e aplicativo mobile.

## Fontes para implementação
- https://github.com/thewh1teagle/kokoro-onnx
- https://github.com/thewh1teagle/kokoro-onnx/blob/main/examples/portuguese.py
- https://pypi.org/project/kokoro-onnx/0.6.1/
- https://github.com/imranpollob/pdf-text-to-speech-reader
- https://github.com/mateogon/pdf-narrator
- https://doc.qt.io/qtforpython-6/PySide6/QtMultimedia/QMediaPlayer.html
- https://pymupdf.readthedocs.io/en/latest/recipes-multiprocessing.html

Usamos APIs e ideias documentadas; este pacote não incorpora integralmente código dos aplicativos pesquisados. Modelos e dependências mantêm suas licenças próprias.

- Privacidade: ORT_DISABLE_TELEMETRY=1 antes do import do runtime e disable_telemetry_events antes de criar a sessão. Não modificar variáveis globais ou políticas do Windows.
