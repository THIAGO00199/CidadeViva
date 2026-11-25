# Cidade Viva — A Living City Simulator

A local-first, multi-agent city and society simulator. The player explores a top-down pixel-art town, talks to fictional residents, and runs controlled scenarios to observe how different profiles respond.

## Prototype 0.4

- An explorable map with keyboard movement, a following camera, and selectable residents.
- 20 initial fictional inhabitants plus the player avatar.
- Persistent SQLite state for population, positions, relationships, events, conversations, and experiments.
- A 24-hour clock, a 360-day calendar, four seasons, and simple daily routines.
- Fictional needs, goals, values, jobs, and a CV$ in-game economy.
- Individual conversations with saved history, powered by a local Ollama model.
- Social experiments with three rounds of influence and per-inhabitant results.
- Optional continuous simulation; the world starts paused.
- Original pixel-art sprites: 21 appearances, four directions, and three walking frames.
- A desktop launcher for starting and stopping local services.

## Architecture

- **Backend:** FastAPI and SQLite.
- **Frontend:** React, TypeScript, and Phaser.
- **Language layer:** Ollama through a local HTTP endpoint.
- **World engine:** deterministic simulation rules that do not require an LLM call for every inhabitant.

The world state and simulation rules are kept separate from the optional language model. This allows the city to continue operating when Ollama is unavailable.

## Run locally

Requirements: Linux x86_64, Python 3.12+, Node.js 20+, and npm. Ollama is optional for conversations that use a local model.

```bash
./scripts/launcher.py
```

Open http://127.0.0.1:5173. To run services without the desktop launcher:

```bash
./scripts/start.sh
./scripts/stop.sh
```

For manual development, see the Portuguese README and [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md).

## Research scope and limitations

This is an exploratory software prototype, not a scientifically validated social or demographic model. Social positions and interactions use explicit heuristics; they are not public-opinion measurements, causal evidence, or predictions about real populations. All residents, events, and currency are fictional.

The SQLite database, logs, virtual environments, frontend build output, and credentials are excluded from Git. Personal progress data is not part of the source repository.

---

[Português](./README.md) · [Español](./README.es.md)
