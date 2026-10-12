# PDF Voz 0.2.8 — caracteres invisíveis e modos de leitura

## Aplicar a atualização

Este pacote incremental exige a instalação 0.2.7 ou 0.2.7.1 existente.

1. Feche o PDF Voz.
2. Extraia o conteúdo do ZIP na pasta que contém ABRIR.bat, mesclando as pastas e substituindo os arquivos correspondentes.
3. Preserve os demais arquivos, o ambiente .venv, os modelos e os dados do usuário. Não é necessário reinstalar dependências.
4. Execute ABRIR.bat e reabra o PDF para refazer a extração.
5. Em Configurações → Modo de leitura, escolha o tratamento desejado.

O progresso é remapeado quando a segmentação muda. O trecho salvo começa novamente do início, pois o tempo de áudio anterior pode não corresponder ao texto corrigido.

## Modos

- **Comum — livros e documentos:** conserva pontuação para interpretação do sintetizador, sem expandir operadores em palavras; mantém tratamento de valores em reais e milhares brasileiros.
- **Técnica — símbolos e programação:** explicita operadores, delimitadores e números como código. A escolha se aplica a todo o livro, inclusive à prosa.
- **Automático — texto e código:** utiliza a classificação extraída do PDF para alternar entre prosa, títulos e código. É um bom ponto de partida para livros que misturam explicações e exemplos. A classificação é heurística e pode errar.

A escolha é salva por livro. A opção antiga Prosa passa a Comum; Código continua como Técnica. Trocar o modo descarta o áudio preparado e prepara novamente o trecho atual. Nenhum modelo novo é carregado.

## Correção

`leitor/text_cleaning.py` centraliza a remoção de caracteres Unicode de controle/formatação, incluindo U+200B, BOM e hífen condicional. Preserva acentos, operadores, tabulações, quebras de linha e sequências literais como `\u200b` escritas em código.

`leitor/pdf_service.py` aplica a limpeza às palavras e às linhas extraídas e atualiza a revisão de extração. Palavras vazias não chegam à segmentação.

`leitor/narration.py` repete a limpeza antes da preparação de fala, implementa o modo comum e atualiza a revisão do áudio.

`leitor/window.py` apresenta os três modos, recupera a escolha por livro e filtra trechos vazios antes da fila de voz, preservando regiões de destaque. Inclui os botões de zoom + e − da correção 0.2.7.1.

`leitor/__init__.py` atualiza a versão. README.md e README_LEITOR.md atualizam as instruções. Os arquivos em tests/ validam os comportamentos e não são necessários para executar o leitor.

Não foi acrescentada dependência, chamada de API ou alteração no motor de voz. A limpeza não corrige problemas de OCR, ordenação de colunas nem todos os casos sem fonemas possíveis no sintetizador.

## Validação realizada

76 testes automatizados aprovados no Linux, com Qt em modo offscreen. Incluem preservação de símbolos/acentos, limpeza antes da síntese, descarte de trechos invisíveis, livro inteiramente vazio, modos, persistência, migração da opção antiga, pausa, recuperação e zoom.

O teste de síntese usa um modelo simulado; não comprova qualidade auditiva. A reprodução real com Kokoro e a interface nativa do Windows devem ser conferidas no computador de uso, sobretudo na passagem que antes apresentava o erro.

Comando de commit sugerido (mensagem): Atualiza PDF Voz para 0.2.8 com modos de leitura e limpeza de caracteres invisíveis
