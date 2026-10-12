# PDF Voz 0.2.9

Leitor local de PDFs em português para Windows 11 x64. A versão 0.2.6 reorganiza a interface com painel lateral recolhível e configurações em janela própria. Mantém a instalação unificada, o motor de voz, as quatro threads de CPU e a preparação de áudio durante a pausa.

## Pronúncias e comparação A/B — 0.2.9

Esta atualização adiciona uma base global em `leitor/data/pronuncias_pt_br.json`, regras conservadoras de abreviações, horários e unidades, e a tela **Configurações → Testar pronúncia**. Inclui 18 frases de avaliação. As quatro adaptações de termos já existentes foram transferidas para o dicionário; palavras ambíguas continuam inativas. Não foram adicionadas exceções por livro nem transcrições fonéticas automáticas dos manuais.

Na tela de teste, escolha uma frase, modo e voz, confira ou edite o texto preparado e clique em Preparar comparação. Ouça A e B. Alterações nessa tela são temporárias e não entram automaticamente no dicionário. Ao abrir o teste, o leitor pausa e encerra a inferência do livro para evitar dois modelos concorrentes. Os WAVs de teste são temporários e a leitura do livro só volta quando você clicar em Continuar.

Pacote cumulativo para instalações 0.2.7 a 0.2.8.1: feche o programa, extraia na raiz junto a ABRIR.bat e substitua os arquivos, incluindo a nova pasta leitor/data. Reabra o PDF. Não reinstale dependências nem apague modelos. Consulte [o guia da versão](docs/PRONUNCIAS_v0_2_9.md).

## Correção de marcadores de lista — 0.2.8.1

Marcadores tipográficos como • e ● no início de itens de texto deixam de ser enviados à voz. Os tópicos são separados em trechos, preservando o texto exibido e suas regiões no PDF. Símbolos no meio de expressões e linhas classificadas como código são preservados. A identificação depende do texto e da estrutura extraídos do PDF.

Este pacote inclui também as alterações da 0.2.8 e a correção de zoom. Pode ser aplicado sobre 0.2.7, 0.2.7.1 ou 0.2.8. Feche o aplicativo, extraia na raiz junto a ABRIR.bat, substitua os arquivos e reabra o PDF para recalcular os trechos. Não reinstale dependências nem remova modelos.

Veja [detalhes da correção](docs/LISTAS_v0_2_8_1.md).

## Atualização 0.2.7 ou 0.2.7.1 → 0.2.8

Feche o leitor e extraia o pacote 0.2.8 na raiz do projeto, junto de `ABRIR.bat`, mesclando as pastas e substituindo os arquivos. Não remova `.venv`, modelos ou dados do usuário. Abra `ABRIR.bat` e reabra o PDF para recalcular a extração.

A correção remove caracteres invisíveis como U+200B antes de preparar a fala e descarta trechos que ficam vazios. Em **Configurações → Modo de leitura**, escolha Comum (livros e documentos), Técnica (símbolos e programação) ou Automático (texto e código). A escolha é salva por livro. O pacote inclui os botões de zoom da 0.2.7.1. Não há dependências novas nem necessidade de reinstalação.

Veja [detalhes e validação da versão 0.2.8](docs/LEITURA_v0_2_8.md).

## Atualização de leitura 0.2.6 → 0.2.7

Feche o leitor e extraia o pacote de leitura na raiz da instalação 0.2.6, mesclando as pastas. Abra ABRIR.bat. Não é necessário reinstalar bibliotecas ou modelos. O layout 0.2.6 é mantido.

As pausas agora consideram títulos e transições entre prosa e código. A divisão interna de texto prioriza pontuação, mantendo o limite de 320 caracteres por chamada. Grupos de zeros à esquerda em números de código são explicitados. A revisão do áudio mudou: ao reabrir o PDF, o trecho salvo recomeça do início para evitar um deslocamento de tempo incompatível.

Veja [alterações e validação da leitura](docs/LEITURA_v0_2_7.md). A comparação auditiva deve ser feita no Windows com a mesma passagem, voz e velocidade. Não há promessa de eliminar toda a entonação mecânica do modelo.

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
