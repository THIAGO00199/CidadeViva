# Arquitetura — Cidade Viva

## Visão geral

Cidade Viva combina três camadas independentes:

1. **Mundo persistente:** SQLite guarda habitantes, posições, relógio, relações, eventos, memórias e experimentos.
2. **Motor de simulação:** regras determinísticas avançam o mundo sem precisar chamar um modelo de linguagem para cada personagem.
3. **Camada de linguagem:** Ollama atende conversas individuais e, futuramente, sínteses de cenários. A indisponibilidade do modelo não deve apagar nem interromper o estado do mundo.

## Componentes atuais

### Backend

FastAPI em backend/app/main.py.

- citizens: identidade, idade, ocupação, biografia, personalidade, posição e estado de vida.
- world: data, hora e estação atual.
- relationships: vínculos direcionados com intensidade.
- world_events: acontecimentos registrados no diário.
- conversations: histórico persistente de diálogos.
- agent_memories: memórias episódicas de conversas e encontros sociais, recuperadas no contexto do chat.
- social_interactions: registro temporal de encontros entre habitantes.
- economy_transactions: livro-razão de renda, despesas básicas e refeições.
- current_activity: atividade atual derivada da agenda e da profissão.
- experiments: pergunta, premissas e estado do cenário.
- simulation_runs, simulation_agents e simulation_messages: rodadas, posições individuais e influência social.
- knowledge_nodes e knowledge_edges: estrutura inicial do grafo de conhecimento.

### Frontend

React + TypeScript + Phaser.

- O mapa é top-down e a câmera acompanha o avatar.
- O avatar usa teclado e persiste posição no backend.
- Habitantes são selecionáveis pelo mapa ou lista.
- Spritesheets originais têm 21 aparências, quatro direções e três quadros por direção; o avatar anima ao caminhar.
- O perfil mostra atividade atual, necessidades, valores, objetivos, família e lembranças recentes.
- Conversas carregam histórico, relações e memórias relevantes.
- Um inicializador Tkinter abre em janela própria e controla os serviços locais.
- O painel de experimentos registra cenários, executa rodadas e apresenta resultados.

### Modelo local

O serviço usa a API OpenAI-compatible do Ollama em 127.0.0.1:11435 por padrão. O modelo configurável inicial é qwen2.5:3b.

A máquina de desenvolvimento tem memória limitada. Por isso, o projeto não deve carregar múltiplos modelos grandes nem gerar chamadas contínuas de LLM para todos os habitantes. O modelo é solicitado apenas em interações que precisam de linguagem.

## Ciclo do mundo

O botão de avanço executa uma hora simulada. A interface também oferece modo contínuo opcional, com um tick a cada três segundos reais; ele começa pausado:

- Atualiza o relógio e a estação.
- Aplica agendas por horário e profissão: trabalho, estudo, refeições, descanso e encontros na praça.
- A cada hora, atualiza energia, fome, humor e necessidade social.
- Refeições reduzem fome e geram transações; sem saldo, o habitante recebe menos alívio da fome e perde humor.
- Encontros próximos podem gerar conversas, reduzir necessidade social, melhorar humor e fortalecer vínculos.
- Memórias episódicas dos encontros e conversas são recuperadas nos diálogos individuais; o histórico de memórias é limitado para controlar o banco.
- Na virada do dia, processa renda, despesas, idade e eventos de ciclo de vida.
- Eventos relevantes entram no diário da cidade.

O calendário atual usa 360 dias por ano, divididos em quatro estações de 90 dias; a idade dos habitantes avança ao completar cada ano simulado. A mortalidade e os nascimentos usam probabilidades simplificadas, explicitamente configuradas no motor. Não são modelos demográficos calibrados. Energia, fome, humor e socialização são indicadores heurísticos. A economia usa créditos fictícios CV$ e tabelas de renda e despesas criadas para o jogo, sem correspondência com salários ou custo de vida reais.

## Experimentos multiagente

O fluxo atual é:

1. Registrar título, pergunta e premissas.
2. Criar uma rodada vinculada ao experimento.
3. Gerar uma posição inicial para cada habitante ativo com base em traços de personalidade, ocupação, palavras-chave do cenário e uma variação controlada.
4. Executar três rodadas de influência em que cada agente pondera sua posição e a de seus vizinhos.
5. Persistir posições e interações resumidas.
6. Apresentar o agregado e a justificativa individual.

**Limite importante:** a posição atual é calculada por heurísticas, não por uma entrevista LLM de cada agente. O resultado não é previsão, pesquisa de opinião ou evidência causal. O método serve para testar a infraestrutura de agentes, relações, memória, rastreabilidade e comparação de cenários.

## Próximas etapas

### Prioridade 1 — economia e consistência do mundo
- Separar com mais precisão residência, trabalho, escola, serviços e espaços públicos.
- Introduzir estoque, produção, consumo, preços e escassez por estabelecimento.
- Inventário pessoal e necessidades materiais além de dinheiro.
- Tornar rotinas e deslocamentos sensíveis à idade, saúde, clima e acontecimentos.

### Prioridade 2 — agentes com memória e vida social
- Resumir memórias antigas em conhecimento estável, sem perder eventos importantes.
- Fazer informações circularem por conversas, eventos, observação e reputação.
- Modelar conflitos, reconciliação, confiança e afastamento ao longo do tempo.
- Fazer objetivos mudarem conforme experiências e condições de vida.

### Prioridade 3 — motor de experimentos inspirado em MiroFish
- Importar uma ideia, notícia, texto ou conjunto de premissas.
- Decompor o cenário em entidades, fatos, incertezas e relações.
- Criar um ramo isolado do mundo para cada experimento.
- Distribuir informação entre agentes por relações e canais.
- Rodar várias iterações e medir mudanças de posição.
- Comparar cenários com premissas diferentes.
- Gerar relatório com evidências internas, divergências e limitações.

### Prioridade 4 — jogo e interface
- Personalização de avatar com aparência escolhida pelo jogador.
- Animações de habitantes e sprites para objetos, interiores e animais.
- Casas e interiores acessíveis.
- Calendário visual, mapa de relações e árvore genealógica.
- Painel de observação global, sem eliminar a possibilidade de conversar diretamente com qualquer agente.

## Regras de qualidade

- Nenhum evento deve ser apresentado como fato real: todos os personagens e eventos do protótipo são fictícios.
- Guardar dados e parâmetros de cada execução para reprodução.
- Não misturar estado do mundo principal com ramos experimentais.
- Não afirmar que um resultado representa a sociedade real.
- Preferir algoritmos baratos e auditáveis; reservar LLM para linguagem e raciocínio contextual em que agreguem valor.
