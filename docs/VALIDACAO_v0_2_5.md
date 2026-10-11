# Validação 0.2.5 — 11/10/2026

Base analisada: `758e19368429e7d647d8683d3799ae39055740ce`. Ambiente de verificação: Linux, Python 3.12, Qt em modo offscreen. Não houve execução dos arquivos BAT no Windows.

## Verificações executadas

- 55 testes automatizados aprovados: 46 do leitor e 9 novos de instalação/modelos.
- Testes do instalador simulam criação/reaproveitamento do ambiente, seleção do Python, ferramentas opcionais e falha de pip. Não executam pip nem criam um ambiente Windows real.
- Testes de modelos verificam reaproveitamento sem download, conferência de integridade local e remoção de download incompleto, com arquivos temporários e rede simulada.
- Teste de processo isolado confirma que preparar modelos não importa Qt, pypdf ou o teste antigo.
- Resolução real pelo pip com `--dry-run --ignore-installed --only-binary=:all: --platform win_amd64 --python-version 3.12`: requisitos principais e opcionais resolvidos com sucesso. Verifica metadados e disponibilidade de distribuições compatíveis, não a execução das DLLs.
- A suíte existente cobre controlador Qt, segmentação, pronúncia textual, armazenamento, extração em processo separado, recuperação de falhas e escrita de WAV. Síntese nos testes de WAV usa motor simulado.

As bibliotecas de apoio da suíte foram instaladas num diretório temporário separado. O ambiente de teste não reproduz integralmente as versões do conjunto Windows e não contém o modelo Kokoro real. Portanto, estes resultados não substituem a validação de voz e instalação no computador do usuário.

## Conferir no Windows

1. Atualização: fechar leitor, preservar cópia anterior, sobrepor os arquivos, manter `.venv` e `models`, executar INSTALAR e ABRIR.
2. Confirmar que o instalador chega ao fim e reaproveita os modelos existentes. Conferir `logs/instalacao.txt` em caso de erro.
3. Abrir PDF, ouvir uma frase, testar pausa/preparação, retomada, volume, dispositivo e histórico salvo.
4. Instalação nova: testar numa pasta sem `.venv` e sem modelos, com Python 3.12 x64 e internet. Idealmente usar um ambiente Windows limpo separado da instalação de uso diário.
5. Se usar o teste antigo, instalar a opção `--ferramentas` e executar seu atalho.

Sem construção de executável nesta etapa. Sem alteração publicada no GitHub por esta validação.
