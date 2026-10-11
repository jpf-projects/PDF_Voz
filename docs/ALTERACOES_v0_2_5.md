# Alterações 0.2.5

Base: commit `758e19368429e7d647d8683d3799ae39055740ce`, versão interna 0.2.4.

Instalação unificada em `instalar.py`, com um comando para dependências, verificação `pip check`, modelos e imports nativos. `leitor/assets.py` concentra a preparação dos modelos e `leitor/preparar.py` permite executá-la sem importar o teste antigo. Downloads e modelos preservam as regras anteriores de integridade local; não são assinaturas do publicador.

Versões centralizadas em constraints, dependências diretas no requirements principal e `pypdf` opcional. Instalações antigas podem continuar tendo pypdf; o instalador não desinstala pacotes. O teste antigo passou para `ferramentas/testar_voz.py`; módulos de compatibilidade preservam imports e atalhos anteriores.

Guias atuais revisados para versão, quatro threads, preparação durante a pausa e modos de narração. Guias antigos arquivados. Nenhuma mudança no modelo, na síntese, na segmentação ou no banco de dados.

## Atualização por ZIP e limpeza

Sobrepor um ZIP não remove arquivos antigos. Por isso os atalhos anteriores foram mantidos como redirecionamentos seguros, em vez de removidos imediatamente. Os arquivos `LEIA_PRIMEIRO_v0_2_2.txt`, `LEIA_PRIMEIRO_v0_2_3.txt` e `LEIA_PRIMEIRO_v0_2_4.txt`, se permanecerem na raiz após a cópia, podem ser excluídos: suas cópias estão em `docs/historico`. Não é preciso apagar mais nada para usar a atualização.

O ZIP não inclui `.venv`, modelos, logs, resultados, arquivos Git ou o WAV de demonstração Linux. A referência anterior permanece no commit base. O executável para Windows ainda não foi construído.
