import { lazy, Suspense, useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import type { Citizen } from "./game/CityScene";

const CityCanvas = lazy(() => import("./components/CityCanvas"));
const API = "http://127.0.0.1:8000/api";

type World = {
  day: number;
  hour: number;
  season: string;
  year: number;
  population: number;
  total_people_ever: number;
};

type Message = { speaker: string; message: string };
type MemoryEntry = { summary: string; importance: number; created_at: string };
type FamilyMember = { id: number; name: string; age: number; profession: string; alive: number };
type FamilyDetails = {
  parents: FamilyMember[];
  partners: FamilyMember[];
  children: FamilyMember[];
  siblings: FamilyMember[];
};
type WorldEvent = { id: number; title: string; description: string; day: number; year: number };
type Experiment = { id: number; title: string; question: string; status: string; assumptions: string[] };
type AgentResult = {
  id: number;
  name: string;
  age: number;
  profession: string;
  initial_stance: number;
  final_stance: number;
  rationale: string;
  position: "favorável" | "cautelosa" | "indefinida";
};
type ExperimentResults = {
  experiment: { id: number; title: string; question: string };
  run: { id: number; rounds: number; created_at: string } | null;
  summary: {
    population: number;
    favorable: number;
    cautious: number;
    neutral: number;
    rounds: number;
    interpretation: string;
  } | null;
  agents: AgentResult[];
};

export default function App() {
  const [citizens, setCitizens] = useState<Citizen[]>([]);
  const [world, setWorld] = useState<World | null>(null);
  const [selected, setSelected] = useState<Citizen | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [family, setFamily] = useState<FamilyDetails | null>(null);
  const [memories, setMemories] = useState<MemoryEntry[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [view, setView] = useState<"people" | "experiments">("people");
  const [events, setEvents] = useState<WorldEvent[]>([]);
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [experimentTitle, setExperimentTitle] = useState("");
  const [experimentQuestion, setExperimentQuestion] = useState("");
  const [experimentAssumptions, setExperimentAssumptions] = useState("");
  const [creatingExperiment, setCreatingExperiment] = useState(false);
  const [runningExperiment, setRunningExperiment] = useState(false);
  const [activeExperiment, setActiveExperiment] = useState<number | null>(null);
  const [results, setResults] = useState<ExperimentResults | null>(null);
  const [notice, setNotice] = useState("");

  const refresh = useCallback(async () => {
    try {
      const [citizenResponse, cityResponse] = await Promise.all([
        fetch(API + "/citizens"),
        fetch(API + "/city")
      ]);
      if (!citizenResponse.ok || !cityResponse.ok) throw new Error("API indisponível");
      const [citizenData, cityData] = await Promise.all([
        citizenResponse.json(),
        cityResponse.json()
      ]);
      setCitizens(citizenData);
      setSelected((current) =>
        current ? citizenData.find((person: Citizen) => person.id === current.id) ?? null : null
      );
      setWorld(cityData);
    } catch {
      setNotice("Conectando ao servidor local...");
    }
  }, []);

  const loadEvents = useCallback(async () => {
    try {
      const response = await fetch(API + "/events?limit=8");
      if (response.ok) setEvents(await response.json());
    } catch {
      // O mapa continua utilizável mesmo sem o painel de eventos.
    }
  }, []);

  const loadExperiments = useCallback(async () => {
    try {
      const response = await fetch(API + "/experiments");
      if (response.ok) setExperiments(await response.json());
    } catch {
      // O painel de experimentos volta a carregar quando a API estiver disponível.
    }
  }, []);

  useEffect(() => {
    refresh();
    loadEvents();
    loadExperiments();
    const timer = window.setInterval(refresh, 5000);
    return () => window.clearInterval(timer);
  }, [refresh, loadEvents, loadExperiments]);

  const choose = useCallback(async (citizen: Citizen) => {
    setSelected(citizen);
    setView("people");
    setMessages([]);
    setFamily(null);
    setMemories([]);
    setNotice("");
    try {
      const [historyResponse, familyResponse, memoryResponse] = await Promise.all([
        fetch(API + "/citizens/" + citizen.id + "/history"),
        fetch(API + "/citizens/" + citizen.id + "/family"),
        fetch(API + "/citizens/" + citizen.id + "/memories")
      ]);
      if (historyResponse.ok) setMessages(await historyResponse.json());
      if (familyResponse.ok) setFamily(await familyResponse.json());
      if (memoryResponse.ok) setMemories(await memoryResponse.json());
    } catch {
      setNotice("Não foi possível carregar o histórico e os vínculos familiares.");
    }
  }, []);

  const savePlayerPosition = useCallback((x: number, y: number) => {
    void fetch(API + "/player/move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ x: Number(x.toFixed(3)), y: Number(y.toFixed(3)) })
    }).catch(() => undefined);
  }, []);

  async function talk(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected || !draft.trim() || busy) return;
    const citizen = selected;
    const text = draft.trim();
    setDraft("");
    setMessages((current) => [...current, { speaker: "Você", message: text }]);
    setBusy(true);
    setNotice("");
    try {
      const response = await fetch(API + "/citizens/" + citizen.id + "/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Falha no diálogo");
      setMessages((current) => [...current, { speaker: citizen.name, message: data.answer }]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        { speaker: "Sistema", message: error instanceof Error ? error.message : "Erro no diálogo." }
      ]);
    } finally {
      setBusy(false);
    }
  }

  async function advance() {
    try {
      const response = await fetch(API + "/tick", { method: "POST" });
      if (!response.ok) throw new Error("Não foi possível avançar o relógio.");
      setWorld(await response.json());
      await Promise.all([refresh(), loadEvents()]);
    } catch {
      setNotice("O relógio não avançou. Verifique o servidor local.");
    }
  }

  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(async () => {
      try {
        const response = await fetch(API + "/tick", { method: "POST" });
        if (!response.ok) throw new Error("Falha no relógio.");
        setWorld(await response.json());
        await Promise.all([refresh(), loadEvents()]);
      } catch {
        setPlaying(false);
        setNotice("A simulação foi pausada porque o servidor não respondeu.");
      }
    }, 3000);
    return () => window.clearInterval(timer);
  }, [playing, refresh, loadEvents]);

  async function createExperiment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (creatingExperiment || experimentTitle.trim().length < 2 || experimentQuestion.trim().length < 8) return;
    setCreatingExperiment(true);
    setNotice("");
    try {
      const assumptions = experimentAssumptions
        .split("\n")
        .map((item) => item.trim())
        .filter(Boolean);
      const response = await fetch(API + "/experiments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: experimentTitle.trim(),
          question: experimentQuestion.trim(),
          assumptions
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Falha ao criar experimento.");
      setActiveExperiment(data.id);
      setResults(null);
      setExperimentTitle("");
      setExperimentQuestion("");
      setExperimentAssumptions("");
      await loadExperiments();
      await loadEvents();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Erro ao criar experimento.");
    } finally {
      setCreatingExperiment(false);
    }
  }

  async function runExperiment(experimentId: number) {
    setRunningExperiment(true);
    setNotice("");
    setActiveExperiment(experimentId);
    try {
      const response = await fetch(API + "/experiments/" + experimentId + "/simulate", {
        method: "POST"
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Falha na simulação.");
      setResults(data);
      await Promise.all([loadExperiments(), loadEvents()]);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Erro na simulação.");
    } finally {
      setRunningExperiment(false);
    }
  }

  async function openExperiment(experimentId: number) {
    setActiveExperiment(experimentId);
    setResults(null);
    try {
      const response = await fetch(API + "/experiments/" + experimentId + "/results");
      if (response.ok) setResults(await response.json());
    } catch {
      setNotice("Não foi possível carregar os resultados.");
    }
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <div className="eyebrow">SIMULADOR DE CIVILIZAÇÃO · AMBIENTE LOCAL</div>
          <h1>CIDADE VIVA</h1>
          <p className="header-subtitle">Uma cidade, milhares de histórias possíveis.</p>
        </div>
        <div className="world-stats">
          <div><small>ANO</small><b>{world?.year ?? 1}</b></div>
          <div><small>ESTAÇÃO · DIA</small><b>{world?.season ?? "Primavera"} · {world?.day ?? 1}</b></div>
          <div><small>HORÁRIO</small><b>{String(world?.hour ?? 8).padStart(2, "0")}:00</b></div>
          <div><small>POPULAÇÃO</small><b>{world?.population ?? 20}</b></div>
          <div className="time-controls">
            <button className={playing ? "pause-button" : "play-button"} onClick={() => setPlaying((current) => !current)}>
              {playing ? "Pausar simulação" : "Iniciar simulação"}
            </button>
            <button className="advance-button" onClick={advance}>Avançar 1 hora <span>→</span></button>
          </div>
        </div>
      </header>

      {notice && <div className="notice" role="status">{notice}</div>}

      <section className="layout">
        <div className="main-column">
          <div className="world-panel">
            <div className="panel-title">
              <span>◈ MUNDO EXPLORÁVEL</span>
              <span className="map-instructions">WASD / SETAS PARA ANDAR · CLIQUE EM UM HABITANTE</span>
            </div>
            <Suspense fallback={<div className="map-loading">Preparando o mapa...</div>}>
              <CityCanvas
                citizens={citizens}
                onSelect={choose}
                onMove={savePlayerPosition}
              />
            </Suspense>
            <div className="world-footer">
              <span>Seu avatar está no mundo. Os moradores seguem suas próprias rotinas.</span>
              <span>{world?.total_people_ever ?? 21} pessoas já fizeram parte da cidade</span>
            </div>
          </div>

          <section className="events-panel">
            <div className="section-heading">
              <span>DIÁRIO DA CIDADE</span>
              <span>ACONTECIMENTOS RECENTES</span>
            </div>
            {events.length ? (
              <div className="event-list">
                {events.slice(0, 4).map((item) => (
                  <article className="event-item" key={item.id}>
                    <span className="event-date">{String(item.day).padStart(2, "0")} · A{item.year}</span>
                    <div><b>{item.title}</b><p>{item.description}</p></div>
                  </article>
                ))}
              </div>
            ) : <p className="empty-state">A cidade ainda está escrevendo sua história.</p>}
          </section>
        </div>

        <aside className="side-panel">
          <div className="panel-tabs">
            <button className={view === "people" ? "tab active" : "tab"} onClick={() => setView("people")}>
              Habitantes
            </button>
            <button className={view === "experiments" ? "tab active" : "tab"} onClick={() => setView("experiments")}>
              Experimentos
            </button>
          </div>

          {view === "people" ? (
            <>
              <div className="panel-title compact-title">
                <span>HABITANTES</span><span>{citizens.filter((c) => !c.is_player).length} ATIVOS</span>
              </div>
              <div className="citizen-list">
                {citizens.filter((citizen) => !citizen.is_player).map((citizen) => (
                  <button
                    className={selected?.id === citizen.id ? "citizen active" : "citizen"}
                    key={citizen.id}
                    onClick={() => choose(citizen)}
                  >
                    <b>{citizen.name}</b>
                    <small>{citizen.age} anos · {citizen.profession}</small>
                  </button>
                ))}
              </div>
              <div className="chat">
                <div className="panel-title compact-title">
                  {selected ? "CONVERSAR · " + selected.name : "CONVERSA"}
                </div>
                {selected ? (
                  <>
                    <div className="citizen-bio">
                      <p>{selected.bio}</p>
                      <small>PERSONALIDADE · {selected.personality}</small>
                      <div className="activity-now">
                        <span>AGORA</span>
                        <b>{selected.current_activity || "Em casa"}</b>
                      </div>
                      <div className="character-goals">
                        <div><span>VALORES</span><b>{selected.core_values?.join(" · ") || "Em formação"}</b></div>
                        <div><span>OBJETIVOS</span><b>{selected.goals?.join(" · ") || "Construindo objetivos"}</b></div>
                        <div className="character-money"><span>DINHEIRO DISPONÍVEL</span><b>CV$ {(selected.money ?? 0).toFixed(0)}</b></div>
                      </div>
                      <div className="family-links">
                        <div className="family-title">VÍNCULOS FAMILIARES</div>
                        {family ? ([
                          ["Pais", family.parents],
                          ["Parceiros", family.partners],
                          ["Filhos", family.children],
                          ["Irmãos", family.siblings]
                        ] as [string, FamilyMember[]][]).map(([label, members]) => (
                          <div className="family-row" key={label}>
                            <span>{label}</span>
                            <b>
                              {members.length
                                ? members.map((member) =>
                                    member.name + (member.alive ? "" : " · falecido")
                                  ).join(", ")
                                : "—"}
                            </b>
                          </div>
                        )) : <span>Carregando vínculos...</span>}
                      </div>
                      <div className="memory-list">
                        <div className="family-title">LEMBRANÇAS RECENTES</div>
                        {memories.length ? memories.slice(0, 4).map((memory, index) => (
                          <div className="memory-item" key={index}>{memory.summary}</div>
                        )) : <div className="memory-empty">Ainda está construindo suas lembranças.</div>}
                      </div>
                      <div className="needs-grid">
                        {([
                          ["Humor", selected.mood],
                          ["Energia", selected.energy],
                          ["Fome", selected.hunger],
                          ["Social", selected.social_need]
                        ] as [string, number | undefined][]).map(([label, value]) => {
                          const percent = Math.round(Math.max(0, Math.min(1, value ?? 0)) * 100);
                          return (
                            <div className="need-item" key={label}>
                              <div><span>{label}</span><b>{percent}%</b></div>
                              <div className="need-track"><i style={{ width: percent + "%" }} /></div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                    <div className="messages">
                      {messages.map((message, index) => (
                        <div className={message.speaker === "Você" ? "msg mine" : "msg"} key={index}>
                          <b>{message.speaker}</b><p>{message.message}</p>
                        </div>
                      ))}
                      {busy && <div className="typing">A pessoa está pensando...</div>}
                    </div>
                    <form onSubmit={talk} className="chat-form">
                      <input
                        value={draft}
                        onChange={(event) => setDraft(event.target.value)}
                        placeholder="Comece uma conversa..."
                        disabled={busy}
                        maxLength={2000}
                      />
                      <button disabled={busy || !draft.trim()}>Enviar</button>
                    </form>
                  </>
                ) : (
                  <p className="hint">Selecione alguém na lista ou clique em um personagem no mapa para conhecer sua história.</p>
                )}
              </div>
            </>
          ) : (
            <div className="experiment-view">
              <div className="panel-title compact-title">TESTAR UMA IDEIA NA CIDADE</div>
              <p className="experiment-intro">
                Registre um cenário e observe como diferentes perfis fictícios reagem a ele.
              </p>
              <form onSubmit={createExperiment} className="experiment-form">
                <label htmlFor="experiment-title">Nome do cenário</label>
                <input
                  id="experiment-title"
                  value={experimentTitle}
                  onChange={(event) => setExperimentTitle(event.target.value)}
                  placeholder="Ex.: Uma nova linha de transporte"
                  maxLength={100}
                />
                <label htmlFor="experiment-question">Pergunta ou proposta</label>
                <textarea
                  id="experiment-question"
                  value={experimentQuestion}
                  onChange={(event) => setExperimentQuestion(event.target.value)}
                  placeholder="O que aconteceria se a cidade..."
                  rows={4}
                  maxLength={2000}
                />
                <label htmlFor="experiment-assumptions">Premissas (uma por linha)</label>
                <textarea
                  id="experiment-assumptions"
                  value={experimentAssumptions}
                  onChange={(event) => setExperimentAssumptions(event.target.value)}
                  placeholder={"Há orçamento limitado\nA mudança começa no próximo ano"}
                  rows={3}
                  maxLength={1500}
                />
                <button className="primary-action" disabled={creatingExperiment}>
                  {creatingExperiment ? "Registrando..." : "Criar experimento"}
                </button>
              </form>

              <div className="experiment-history">
                <div className="section-heading"><span>CENÁRIOS REGISTRADOS</span></div>
                {experiments.length ? experiments.map((experiment) => (
                  <article
                    className={activeExperiment === experiment.id ? "experiment-card selected" : "experiment-card"}
                    key={experiment.id}
                  >
                    <button className="experiment-open" onClick={() => openExperiment(experiment.id)}>
                      <b>{experiment.title}</b>
                      <small>{experiment.status === "simulated" ? "SIMULADO" : "RASCUNHO"}</small>
                      <p>{experiment.question}</p>
                    </button>
                    <button
                      className="run-button"
                      onClick={() => runExperiment(experiment.id)}
                      disabled={runningExperiment}
                    >
                      {runningExperiment && activeExperiment === experiment.id ? "Simulando..." : "Simular"}
                    </button>
                  </article>
                )) : <p className="empty-state">Nenhum cenário registrado.</p>}
              </div>

              {results?.summary && (
                <section className="results-panel">
                  <div className="section-heading"><span>RESULTADO · {results.experiment.title}</span></div>
                  <div className="result-counts">
                    <div><b>{results.summary.favorable}</b><small>Favoráveis</small></div>
                    <div><b>{results.summary.cautious}</b><small>Cautelosos</small></div>
                    <div><b>{results.summary.neutral}</b><small>Indefinidos</small></div>
                  </div>
                  <p className="caveat">{results.summary.interpretation}</p>
                  <div className="agent-results">
                    {results.agents.map((agent) => (
                      <article className="agent-result" key={agent.id}>
                        <div><b>{agent.name}</b><small>{agent.profession}</small></div>
                        <span className={"stance " + agent.position.replace("á", "a")}>{agent.position}</span>
                        <p>{agent.rationale}</p>
                      </article>
                    ))}
                  </div>
                </section>
              )}
            </div>
          )}
        </aside>
      </section>

      <footer className="app-footer">
        CIDADE VIVA · PROTÓTIPO 0.4 · SIMULAÇÃO FICTÍCIA · MODELO LOCAL VIA OLLAMA
      </footer>
    </main>
  );
}
