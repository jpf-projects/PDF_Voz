# Implementação 0.2

## Componentes

| Arquivo | Responsabilidade |
|---|---|
| leitor_pdf.py | QApplication, trava exclusiva, diretório de dados, logs e encerramento |
| leitor/window.py | Estado da sessão, orquestração do player/fila, UI e navegação |
| leitor/viewer.py | Cena de PDF em pontos, zoom, regiões e clique |
| leitor/domain.py | Segmentação conservadora e contagem de reserva contígua |
| leitor/pdf_service.py | Hash, extração, coordenadas, TOC e renderização |
| leitor/workers.py | Processos spawn isolados e mensagens por filas |
| leitor/voice.py | Adaptador Kokoro/ONNX, CPU, português e validação do WAV |
| leitor/storage.py | SQLite, progresso e limpeza de sessões temporárias |

## Fluxo

UI envia abrir ao processo PDF; este calcula SHA-256, extrai palavras/coordenadas e devolve segmentos. Cada ID é uma sequência estável na versão de extração 1, subordinada ao hash do documento. As regiões guardam página e retângulo em coordenadas não rotacionadas de PyMuPDF; display_box aplica rotation_matrix. A renderização usa o mesmo documento e QGraphicsScene em pontos; somente o visualizador aplica zoom. Há um pedido de renderização em andamento e a solicitação mais recente substitui as pendentes.

Ao reproduzir, o processo de voz carrega Kokoro uma vez, com CPUExecutionProvider, duas threads intra-op e uma inter-op. A UI mantém um único pedido de síntese em andamento. Cada pedido inclui token de navegação, índice e caminho exclusivo. Resultados de tokens anteriores são excluídos e não alteram a seleção. O player e QAudioOutput permanecem na thread Qt.

O buffer soma apenas durações contíguas a partir do trecho atual, desconta o offset e divide pela velocidade. Inicia em 60 segundos (ou fim do livro totalmente pronto) e prepara até aproximadamente 90. Um trecho novo pode ultrapassar ligeiramente o alvo. Trocas automáticas aproveitam o próximo arquivo já pronto; esgotamento retorna a BUFFERING. Pausa desliga intenção de tocar e de agendar novos trabalhos.

## Estados

idle → paused → buffering → loading → playing. Pause preserva intenção desligada; enquanto loading termina, a mídia pode ficar pronta em paused sem iniciar. Erros desligam a intenção e apresentam tentativa novamente. LoadedMedia/seekable são aguardados para restaurar offset. EndOfMedia avança o índice ou marca conclusão. Nenhum estado representa fala palavra por palavra.

## Persistência e limpeza

SQLite contém books (hash/caminho/título/payload), progress (hash/índice/offset/velocidade/página/zoom/concluído) e settings. Arquivos temporários têm nomes internos e uma pasta session_UUID. Na navegação, conservam-se até dois trechos anteriores; num salto, conservam-se apenas índices próximos. Ao encerrar o livro, o processo TTS é encerrado antes da limpeza. Arquivos retidos pelo Windows são tentados novamente e na próxima inicialização. QLockFile impede sessões simultâneas compartilhando o cache.

## Próximas melhorias após teste do usuário

Confirmar desempenho e qualidade por sentença; medir versão quantizada antes de adotá-la; melhorar regras editoriais usando os livros reais; separar mais lógica do controlador quando os comportamentos estabilizarem; adicionar exportação somente mediante escolha explícita. Não há conta, servidor ou LLM.

## Referências técnicas

- https://doc.qt.io/qtforpython-6/PySide6/QtMultimedia/QMediaPlayer.html
- https://pymupdf.readthedocs.io/en/latest/page.html
- https://pymupdf.readthedocs.io/en/latest/recipes-multiprocessing.html
- https://github.com/thewh1teagle/kokoro-onnx
- https://github.com/microsoft/onnxruntime/blob/main/docs/Privacy.md

Bibliotecas e modelos possuem licenças próprias. Esta entrega é para teste local; não é um instalador comercial pronto para distribuição.
