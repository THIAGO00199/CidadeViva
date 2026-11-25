# Cidade Viva — Un simulador de ciudad viva

Simulador local de ciudad y sociedad multiagente. El jugador explora una ciudad en pixel art desde una perspectiva superior, conversa con habitantes ficticios y ejecuta escenarios controlados para observar cómo responden distintos perfiles.

## Prototipo 0.4

- Mapa explorable con movimiento por teclado, cámara que sigue al avatar y habitantes seleccionables.
- 20 habitantes ficticios iniciales más el avatar del jugador.
- Estado persistente en SQLite para población, posiciones, relaciones, eventos, conversaciones y experimentos.
- Reloj de 24 horas, calendario de 360 días, cuatro estaciones y rutinas diarias sencillas.
- Necesidades, objetivos, valores, profesiones y economía ficticia en créditos CV$.
- Conversaciones individuales con historial guardado mediante un modelo local de Ollama.
- Experimentos sociales con tres rondas de influencia y resultados por habitante.
- Simulación continua opcional; el mundo comienza pausado.
- Sprites originales: 21 apariencias, cuatro direcciones y tres cuadros de caminata.
- Inicializador de escritorio para gestionar los servicios locales.

## Arquitectura

- **Backend:** FastAPI y SQLite.
- **Frontend:** React, TypeScript y Phaser.
- **Capa de lenguaje:** Ollama mediante un endpoint HTTP local.
- **Motor del mundo:** reglas deterministas que no requieren una llamada a un LLM por cada habitante.

El estado del mundo y las reglas de simulación están separados del modelo de lenguaje opcional. Así, la ciudad puede seguir funcionando cuando Ollama no está disponible.

## Ejecución local

Requisitos: Linux x86_64, Python 3.12+, Node.js 20+ y npm. Ollama es opcional para las conversaciones que utilizan un modelo local.

```bash
./scripts/launcher.py
```

Abre http://127.0.0.1:5173. Para iniciar los servicios sin el inicializador de escritorio:

```bash
./scripts/start.sh
./scripts/stop.sh
```

Para desarrollo manual, consulta el README en portugués y [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md).

## Alcance y limitaciones

Es un prototipo exploratorio de software, no un modelo social o demográfico validado científicamente. Las posiciones e interacciones sociales utilizan heurísticas explícitas; no son mediciones de opinión pública, evidencia causal ni predicciones sobre poblaciones reales. Todos los habitantes, eventos y la moneda son ficticios.

La base SQLite, los registros, los entornos virtuales, los archivos compilados del frontend y las credenciales están excluidos de Git. Los datos personales de uso no forman parte del repositorio de código.

---

[Português](./README.md) · [English](./README.en.md)
