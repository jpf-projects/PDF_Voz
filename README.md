# PDF Voz 0.2.6

Leitor local de PDFs em português para Windows 11 x64. A versão 0.2.6 reorganiza a interface com painel lateral recolhível e configurações em janela própria. Mantém a instalação unificada, o motor de voz, as quatro threads de CPU e a preparação de áudio durante a pausa.

## Atualização de layout 0.2.5 → 0.2.6

Feche o leitor e extraia o conteúdo do ZIP de layout na raiz do projeto, ao lado de `ABRIR.bat`, mesclando as pastas e substituindo os arquivos. Abra `ABRIR.bat`. Não é necessário executar o instalador novamente: nenhuma dependência mudou. O pacote de layout contém somente arquivos alterados e requer a instalação 0.2.5 existente.

O botão Configurações reúne voz, saída de áudio, reserva, tratamento da leitura e limpeza de áudios. O botão Painel lateral ou Ctrl+B recolhe Trechos/Sumário/Recentes. Fechar livro fica no menu Arquivo. Reprodução, velocidade, volume e início antecipado continuam na janela principal.

Veja [alterações e validação do layout](docs/LAYOUT_v0_2_6.md).

## Primeira instalação

1. Instale Python 3.12 de 64 bits, disponível em https://www.python.org/downloads/windows/ . Não é necessário VS Code.
2. Extraia o pacote completo para uma pasta na qual você possa gravar, como Documentos. Não execute os arquivos dentro do ZIP.
3. Com internet, execute **INSTALAR.bat**. Aguarde a mensagem de instalação concluída.
4. Execute **ABRIR.bat**, abra um PDF e inicie a leitura.

O instalador cria ou reaproveita `.venv`, instala todas as dependências, verifica conflitos, prepara os modelos ausentes e verifica bibliotecas nativas e português brasileiro. Não instala Python automaticamente e não precisa de administrador. O teste final não reproduz som: confira fones/alto-falantes ao abrir o leitor.

Reserve alguns GB livres para Python, bibliotecas, modelos e temporários. Os modelos são os mesmos da versão anterior. Depois da instalação, a leitura funciona sem internet, conta ou chave de API. Não é necessário instalar eSpeak ou CUDA separadamente.

## Atualizar uma instalação existente

Feche o leitor. Faça uma cópia da pasta atual como reserva. Extraia o conteúdo desta atualização **dentro da pasta existente**, ao lado de `leitor_pdf.py`, substituindo os arquivos quando solicitado. Preserve `.venv` e `models`. Não coloque a atualização numa subpasta adicional.

Execute `INSTALAR.bat` uma vez e, depois, `ABRIR.bat`. Os modelos existentes são conferidos e reaproveitados. O instalador não apaga modelos, PDFs, progresso ou preferências. A pasta de dados do aplicativo mantém o mesmo nome e a revisão do áudio não mudou nesta atualização.

Se você usa uma pasta de modelos externa selecionada na interface, o instalador ainda prepara a pasta `models` ao lado do projeto. Para evitar uma segunda cópia, mantenha nesta instalação a pasta de modelos original. O leitor continua aceitando uma pasta externa para leitura.

Os cinco atalhos numerados antigos e as entradas `bootstrap.py`, `instalar_leitor.py` e `app.py` permanecem como compatibilidade. Eles redirecionam às implementações atuais. Não é necessário executá-los em sequência. O arquivo `requirements_leitor.txt` também apenas encaminha à lista principal.

## Ajuda

Em caso de falha, leia a mensagem e `logs/instalacao.txt`. Uma nova execução tenta concluir a instalação; não remove o ambiente existente. Se `.venv` estiver incompatível ou incompleta, renomeie-a para `.venv_anterior` e execute novamente. Isso recria apenas o ambiente de bibliotecas e requer internet.

`ferramentas/DIAGNOSTICO.bat` informa versões mesmo se a interface não abrir. O menu do aplicativo também oferece diagnóstico. Logs do instalador ficam na pasta do projeto; logs de leitura ficam na pasta de dados do usuário.

O teste antigo de voz é opcional: execute `INSTALAR.bat --ferramentas` pelo terminal e, depois, `ferramentas/TESTAR_VOZ.bat`. Ele utiliza `pypdf` e pode criar WAVs permanentes em `resultados`; esses WAVs não são o cache automático do leitor.

## Organização

| Caminho | Função |
| --- | --- |
| `INSTALAR.bat` / `instalar.py` | Instalação completa e reparação |
| `ABRIR.bat` / `leitor_pdf.py` | Abertura do leitor |
| `leitor/` | Interface, PDF, voz, modelos, armazenamento e diagnóstico |
| `requirements.txt` | Dependências diretas |
| `dependencias/constraints.txt` | Versões fixadas, incluindo dependências indiretas |
| `dependencias/ferramentas.txt` | Dependências opcionais do teste antigo |
| `ferramentas/` e `reader/` | Ferramentas e compatibilidade do protótipo |
| `tests/` | Testes de desenvolvimento |
| `docs/` | Arquitetura, validações e histórico |
| `models/` e `.venv/` | Gerados localmente; não enviados ao Git |

A lista de versões foi preservada a partir da 0.2.4 e resolvida para Windows x64/Python 3.12. Não há atualização automática para versões novas. `pip freeze` registra o ambiente realmente instalado em `logs/dependencias_instaladas.txt`. Constraints não substituem testes reais no Windows.

## Desenvolvimento

No terminal, para instalar também as ferramentas de teste:

```powershell
.\INSTALAR.bat --ferramentas
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
.\.venv\Scripts\python.exe leitor_pdf.py
```

Não remova DLLs ou executáveis individuais de `.venv`. Excluir `__pycache__` com o programa fechado é seguro, mas não é necessário para instalar ou atualizar.

Veja [o guia do leitor](README_LEITOR.md), [as alterações](docs/ALTERACOES_v0_2_5.md) e [a validação](docs/VALIDACAO_v0_2_5.md). A criação de executável/instalador sem Python fica para uma etapa futura.
