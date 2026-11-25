# Cidade Viva

Simulador local de cidade e sociedade multiagente. A pessoa jogadora explora um mundo top-down em pixel art, conversa com habitantes e cria cenários para observar como perfis diferentes reagem.

## Estado do projeto

**Protótipo 0.4 — vida social, memórias persistentes, sprites próprios e inicializador desktop.**

- Mapa explorável com WASD/setas, câmera seguindo o avatar e moradores clicáveis.
- 20 habitantes fictícios iniciais + avatar do jogador.
- Banco SQLite persistente para população, posições, relações, eventos, conversas e experimentos.
- Relógio de 24 horas, calendário de 360 dias, quatro estações e rotinas simples de deslocamento.
- Envelhecimento diário, eventos de vida e estrutura inicial para nascimentos e falecimentos.
- Necessidades de energia, fome, humor e socialização, com objetivos e valores pessoais.
- Economia fictícia em créditos CV$, com renda, despesas e extrato de transações.
- Perfis individuais com valores, objetivos e indicadores de necessidades.
- Conversas individuais com histórico salvo, usando um modelo local via Ollama.
- Experimentos com três rodadas de influência social e resultados por habitante.
- Modo contínuo opcional: três segundos reais equivalem a uma hora simulada; o mundo começa pausado.
- Rotinas diárias por profissão e atividade atual exibida no perfil.
- Interações sociais por proximidade, evolução gradual de vínculos e memórias episódicas.
- Conversas com o jogador fortalecem vínculos e deixam lembranças persistentes para os habitantes.
- Sprites pixel-art originais: 21 aparências, quatro direções e três quadros de caminhada.
- Inicializador desktop com janela própria e atalho no menu de aplicativos.

O sistema ainda não é uma simulação científica validada. As opiniões dos experimentos são heurísticas transparentes baseadas em perfil, contexto e relações sociais. Elas servem para exploração e comparação de cenários fictícios, não para prever a realidade nem representar a opinião de uma população real.

## Requisitos

- Linux x86_64 (testado no Garuda Linux)
- Python 3.12+
- Node.js 20+ e npm
- Ollama (opcional; necessário para conversas com IA)
- Memória disponível suficiente para o modelo local escolhido

## Executar localmente

Inicie os serviços em conjunto:

~~~bash
./scripts/launcher.py

# Para iniciar os serviços sem a janela do inicializador:
./scripts/start.sh
~~~

Abra http://127.0.0.1:5173. Para encerrar processos iniciados pelo script:

~~~bash
./scripts/stop.sh
~~~

Os registros ficam em logs/; o banco e os logs não devem entrar no Git.

Para iniciar manualmente, use os comandos abaixo.

Terminal 1 — backend:

~~~bash
cd backend
uv sync
OLLAMA_URL=http://127.0.0.1:11435 OLLAMA_MODEL=qwen2.5:3b uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
~~~

Terminal 2 — frontend:

~~~bash
cd frontend
npm install
npm run dev
~~~

Abra o endereço local informado pelo Vite (normalmente http://127.0.0.1:5173).

O projeto usa SQLite em backend/data/cidade_viva.db. Para mudar o local do banco, defina CIDADE_VIVA_DB.

## API principal

| Método | Rota | Função |
|---|---|---|
| GET | /api/health | Estado do serviço |
| GET | /api/city | Relógio e população |
| GET | /api/citizens | Habitantes vivos |
| POST | /api/player/move | Salvar posição do avatar |
| POST | /api/tick | Avançar uma hora |
| GET | /api/events | Diário da cidade |
| GET | /api/economy | Indicadores econômicos |
| GET | /api/citizens/{id}/economy | Extrato individual |
| GET | /api/relationships | Rede social |
| GET | /api/citizens/{id}/family | Pais, parceiros, filhos e irmãos |
| GET | /api/citizens/{id}/history | Histórico de conversa |
| POST | /api/citizens/{id}/chat | Conversar com um habitante |
| GET/POST | /api/experiments | Listar/criar cenários |
| POST | /api/experiments/{id}/simulate | Executar três rodadas |
| GET | /api/experiments/{id}/results | Ler resultados |
| GET | /api/experiments/{id}/graph | Ler grafo de conhecimento |

## Princípios

1. O SQLite é a fonte de verdade; o LLM não controla o estado do mundo.
2. Regras determinísticas executam relógio, rotinas, envelhecimento e relações.
3. LLM para diálogo sob demanda; não executar uma chamada por habitante a cada hora.
4. Experimentos guardam premissas, rodadas e resultados para comparação.
5. Agentes simulados não são amostra representativa da população real.

Veja docs/ARCHITECTURE.md para a arquitetura e o plano de evolução.
