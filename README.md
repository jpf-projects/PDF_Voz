# PDF Voz 0.2.3

Leitor desktop para abrir PDFs locais e narrar o texto em português, com vozes Dora, Alex e Santa. O processamento de PDF e a síntese de voz acontecem no computador; não é necessária conta nem chave de API.

## Requisitos

- Windows 11 de 64 bits (plataforma-alvo desta versão).
- Python 3.12.x de 64 bits. Pode ser instalado junto com outras versões; não remova o Python que já usa. O instalador verifica a versão e informa se estiver faltando. O instalador oficial está em [python.org/downloads/windows](https://www.python.org/downloads/windows/).
- Internet durante a instalação, para baixar os pacotes Python e os modelos de voz.
- Aproximadamente 2 GB livres como margem de planejamento. Os dois arquivos de modelo ocupam cerca de 338 MiB; o ambiente Python e a interface também usam espaço, e o total varia conforme o sistema.

Esta versão tem o Windows 11 como plataforma-alvo, mas a validação integrada registrada para a 0.2.3 foi executada em Linux; áudio físico e instalação no Windows ainda precisam de confirmação no equipamento.

Não é necessário instalar o eSpeak NG separadamente. A dependência Python `espeakng-loader` fornece a biblioteca e os dados de pronúncia do eSpeak NG usados pelo sintetizador. O aplicativo seleciona essa cópia local, sem exigir instalação global no Windows. Também não é necessário instalar CUDA ou executar como administrador; a inferência usa CPU.

## Baixar e instalar

1. Baixe o ZIP completo da versão distribuída pelo projeto e extraia todos os arquivos para uma pasta local. Não execute os `.bat` de dentro do ZIP.
2. Mantenha a internet conectada e abra `1_INSTALAR.bat`. Ele cria o ambiente isolado `.venv`, instala as dependências de voz e baixa os modelos para `models`. A primeira etapa pode demorar.
3. Quando terminar, abra `4_ATUALIZAR_LEITOR.bat`. Apesar do nome, esse passo também é necessário numa instalação nova: instala as dependências da interface gráfica e do leitor de PDF no mesmo `.venv`.
4. Abra `5_ABRIR_LEITOR.bat` para iniciar o leitor. Clique em **Abrir PDF** e selecione o arquivo.

Não feche a janela de instalação antes de aparecer a mensagem de conclusão. Para instalar novamente após uma falha de rede, execute o respectivo `.bat` outra vez. Os detalhes ficam em `logs/instalacao.txt` ou `logs/instalacao_leitor.txt`.

## Usar depois da instalação

Para as próximas execuções, basta abrir `5_ABRIR_LEITOR.bat`. Os arquivos `.venv` e `models` são necessários: mantenha-os na pasta do projeto. Depois da instalação, a leitura não precisa de internet. Os PDFs não são enviados para servidores.

`2_TESTAR_VOZ.bat` é opcional e abre o teste de voz por menu; não é o leitor de PDFs. `3_DIAGNOSTICO.bat` mostra as versões de Python e dos pacotes instalados.

## Dependências instaladas

O pip instala as versões fixadas nos arquivos de requisitos do projeto. As principais são PySide6 (interface), PyMuPDF (leitura de PDF), kokoro-onnx e ONNX Runtime (síntese), além de phonemizer e espeakng-loader (fonemas e pronúncia). Pacotes de suporte, como NumPy, SoundFile e pypdf, também são instalados automaticamente. Não é preciso instalar esses pacotes manualmente.

## VS Code e ajuda

Para iniciar pelo terminal do VS Code, na pasta do projeto:

```powershell
.\.venv\Scripts\python.exe leitor_pdf.py
```

O guia de controles, limitações e atualizações está em [README_LEITOR.md](README_LEITOR.md). A validação disponível e seus limites estão em [docs/VALIDACAO_v0_2_3.md](docs/VALIDACAO_v0_2_3.md). Em caso de falha, inclua o log da etapa correspondente ao pedir ajuda; revise os caminhos locais antes de compartilhar.
