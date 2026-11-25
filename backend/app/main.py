import json
import os
import random
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .database import connect, init_db

app = FastAPI(title="Cidade Viva API", version="0.4.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:4173", "http://127.0.0.1:4173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11435").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "3072"))


@app.on_event("startup")
def startup():
    init_db()
    with connect() as db:
        world = db.execute("SELECT hour FROM world WHERE id=1").fetchone()
        residents = db.execute(
            "SELECT id,profession,social_need FROM citizens WHERE alive=1 AND is_player=0"
        ).fetchall()
        for person in residents:
            db.execute(
                "UPDATE citizens SET current_activity=? WHERE id=?",
                (_activity_for(person, world["hour"]), person["id"]),
            )
        db.execute(
            "UPDATE citizens SET current_activity='Explorando a cidade' WHERE is_player=1"
        )


class ChatInput(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class MoveInput(BaseModel):
    x: float = Field(ge=1, le=42)
    y: float = Field(ge=1, le=27)


class ExperimentInput(BaseModel):
    title: str = Field(min_length=2, max_length=100)
    question: str = Field(min_length=8, max_length=2000)
    assumptions: list[str] = Field(default_factory=list, max_length=12)


def _event(db, title: str, description: str, day: int, year: int):
    db.execute(
        "INSERT INTO world_events(title,description,day,year) VALUES(?,?,?,?)",
        (title, description, day, year),
    )


def _activity_for(person, hour: int) -> str:
    if hour >= 22 or hour < 6:
        return "Dormindo"
    if hour == 7:
        return "Tomando café da manhã"
    if hour == 8:
        return "Se preparando para o dia"
    if hour in (12, 13):
        return "Almoçando e descansando"
    if hour == 19:
        return "Jantando em casa"
    if hour in (20, 21):
        return "Encontrando vizinhos" if person["social_need"] > 0.48 else "Descansando em casa"
    if not 9 <= hour < 18:
        return "Em casa"
    activities = {
        "Físico teórico": "Pesquisando no laboratório",
        "Médica": "Atendendo pacientes",
        "Professor": "Dando aula",
        "Aposentada": "Cuidando da casa e da comunidade",
        "Estudante": "Estudando",
        "Comerciante": "Atendendo no mercado",
        "Agricultor": "Trabalhando na plantação",
        "Engenheira": "Projetando infraestrutura",
        "Monge": "Em contemplação ou serviço comunitário",
        "Motorista": "Dirigindo pela região",
        "Artista": "Criando no ateliê",
        "Pedreiro": "Trabalhando na obra",
        "Cozinheira": "Preparando refeições",
        "Pesquisador": "Fazendo pesquisa de campo",
        "Costureira": "Trabalhando no ateliê",
        "Desempregado": "Procurando oportunidades",
        "Pessoa em situação de rua": "Procurando um local seguro",
        "Assistente social": "Acompanhando famílias",
        "Criança": "Estudando e brincando",
    }
    return activities.get(person["profession"], "Trabalhando")


def _move_residents(db, hour: int):
    residents = db.execute(
        "SELECT id,x,y,home_x,home_y,work_x,work_y,profession,social_need FROM citizens "
        "WHERE alive=1 AND is_player=0"
    ).fetchall()
    for person in residents:
        activity = _activity_for(person, hour)
        if activity in ("Almoçando e descansando", "Encontrando vizinhos"):
            target_x, target_y = 21.5, 13.5
        elif 9 <= hour < 18:
            target_x, target_y = person["work_x"], person["work_y"]
        else:
            target_x, target_y = person["home_x"], person["home_y"]
        dx = max(-0.85, min(0.85, target_x - person["x"]))
        dy = max(-0.85, min(0.85, target_y - person["y"]))
        db.execute(
            "UPDATE citizens SET x=?,y=?,current_activity=? WHERE id=?",
            (max(1, min(42, person["x"] + dx * 0.38)),
             max(1, min(27, person["y"] + dy * 0.38)), activity, person["id"]),
        )


def _social_life(db, hour: int, day: int, year: int):
    people = db.execute(
        "SELECT id,name,x,y,mood,social_need,current_activity FROM citizens "
        "WHERE alive=1 AND is_player=0 ORDER BY id"
    ).fetchall()
    rng = random.Random(year * 900000 + day * 100 + hour)
    for index, first in enumerate(people):
        for second in people[index + 1:]:
            distance = ((first["x"] - second["x"]) ** 2 + (first["y"] - second["y"]) ** 2) ** 0.5
            if distance > 1.35:
                continue
            chance = 0.10 + max(first["social_need"], second["social_need"]) * 0.28
            if rng.random() > chance:
                continue

            existing = db.execute(
                "SELECT strength,relation FROM relationships WHERE source_id=? AND target_id=? "
                "AND relation IN ('conhecido','amizade','vizinho') ORDER BY strength DESC LIMIT 1",
                (first["id"], second["id"]),
            ).fetchone()
            previous_strength = float(existing["strength"]) if existing else 0.0
            strength = min(0.95, previous_strength + 0.025 + rng.random() * 0.015)
            relation = "amizade" if strength >= 0.62 else ("conhecido" if existing else "vizinho")
            if existing:
                db.execute(
                    "UPDATE relationships SET strength=?,relation=? WHERE source_id=? AND target_id=? AND relation=?",
                    (strength, relation, first["id"], second["id"], existing["relation"]),
                )
            else:
                db.execute(
                    "INSERT OR IGNORE INTO relationships(source_id,target_id,relation,strength) VALUES(?,?,?,?)",
                    (first["id"], second["id"], relation, strength),
                )
            reverse = db.execute(
                "UPDATE relationships SET strength=?,relation=? "
                "WHERE source_id=? AND target_id=? AND relation IN ('conhecido','amizade','vizinho')",
                (strength, relation, second["id"], first["id"]),
            )
            if reverse.rowcount == 0:
                db.execute(
                    "INSERT OR IGNORE INTO relationships(source_id,target_id,relation,strength) VALUES(?,?,?,?)",
                    (second["id"], first["id"], relation, strength),
                )

            place = "na praça" if "Encontrando" in first["current_activity"] or "Almoçando" in first["current_activity"] else "pelo bairro"
            summary = f"{first['name']} conversou com {second['name']} {place}."
            db.execute(
                "INSERT INTO social_interactions(source_id,target_id,day,year,hour,summary) VALUES(?,?,?,?,?,?)",
                (first["id"], second["id"], day, year, hour, summary),
            )
            for person, other in ((first, second), (second, first)):
                db.execute(
                    "INSERT INTO agent_memories(citizen_id,event_id,summary,importance) VALUES(?,NULL,?,?)",
                    (person["id"], f"Conversou com {other['name']} {place}.", 0.38),
                )
                db.execute(
                    "UPDATE citizens SET social_need=MAX(0,social_need-0.16),"
                    "mood=MIN(1,mood+0.025) WHERE id=?",
                    (person["id"],),
                )
                db.execute(
                    "DELETE FROM agent_memories WHERE citizen_id=? AND id NOT IN "
                    "(SELECT id FROM agent_memories WHERE citizen_id=? ORDER BY id DESC LIMIT 30)",
                    (person["id"], person["id"]),
                )
            if existing and previous_strength < 0.62 <= strength:
                _event(db, "Uma amizade se fortalece", summary, day, year)

    db.execute(
        "DELETE FROM social_interactions WHERE id NOT IN "
        "(SELECT id FROM social_interactions ORDER BY id DESC LIMIT 5000)"
    )


def _advance_needs(db, hour: int, day: int, year: int):
    people = db.execute(
        "SELECT id,x,y,energy,hunger,mood,social_need,money FROM citizens WHERE alive=1"
    ).fetchall()
    residents = [(person["x"], person["y"], person["id"]) for person in people]

    for person in people:
        energy = float(person["energy"])
        hunger = float(person["hunger"])
        social = float(person["social_need"])
        mood = float(person["mood"])
        money = float(person["money"])

        sleeping = hour >= 22 or hour < 6
        energy = min(1.0, energy + 0.055) if sleeping else max(0.0, energy - 0.018)
        hunger = min(1.0, hunger + 0.018)

        if hour in (7, 12, 19):
            meal_cost = 1.5
            if money >= meal_cost:
                money -= meal_cost
                hunger = max(0.0, hunger - 0.34)
                db.execute(
                    "INSERT INTO economy_transactions(citizen_id,amount,reason,day,year) "
                    "VALUES(?,?,?,?,?)",
                    (person["id"], -meal_cost, "refeição", day, year),
                )
            else:
                hunger = max(0.0, hunger - 0.12)
                mood = max(0.0, mood - 0.02)

        social = min(1.0, social + 0.012)
        nearby = sum(
            1 for x, y, other_id in residents
            if other_id != person["id"] and abs(x - person["x"]) < 2.0 and abs(y - person["y"]) < 2.0
        )
        if nearby:
            social = max(0.0, social - min(0.12, nearby * 0.018))

        stress = max(0.0, 0.48 - energy) * 0.20
        stress += max(0.0, hunger - 0.65) * 0.25
        stress += max(0.0, social - 0.78) * 0.15
        financial = -0.035 if person["money"] < 0 else (0.018 if person["money"] > 80 else 0.0)
        target_mood = max(0.0, min(1.0, 0.62 - stress + financial))
        mood = max(0.0, min(1.0, mood * 0.94 + target_mood * 0.06))

        db.execute(
            "UPDATE citizens SET energy=?,hunger=?,mood=?,social_need=?,money=? WHERE id=?",
            (energy, hunger, mood, social, money, person["id"]),
        )


def _daily_economy(db, day: int, year: int):
    income_by_job = {
        "Físico teórico": 105.0, "Médica": 125.0, "Professor": 78.0,
        "Comerciante": 68.0, "Agricultor": 58.0, "Engenheira": 118.0,
        "Motorista": 62.0, "Artista": 38.0, "Pedreiro": 72.0,
        "Cozinheira": 48.0, "Pesquisador": 92.0, "Costureira": 44.0,
        "Assistente social": 70.0, "Aposentada": 38.0,
        "Monge": 18.0, "Estudante": 18.0, "Desempregado": 22.0,
        "Pessoa em situação de rua": 10.0, "Criança": 0.0, "Visitante": 0.0,
    }
    expense_by_job = {
        "Criança": 0.0, "Estudante": 15.0, "Aposentada": 22.0,
        "Pessoa em situação de rua": 5.0, "Desempregado": 18.0,
        "Monge": 8.0, "Visitante": 12.0,
    }
    people = db.execute(
        "SELECT id,name,profession,money FROM citizens WHERE alive=1 AND is_player=0"
    ).fetchall()

    for person in people:
        profession = person["profession"]
        income = income_by_job.get(profession, 45.0)
        expense = expense_by_job.get(profession, 28.0)
        if income:
            db.execute(
                "UPDATE citizens SET money=money+? WHERE id=?",
                (income, person["id"]),
            )
            db.execute(
                "INSERT INTO economy_transactions(citizen_id,amount,reason,day,year) "
                "VALUES(?,?,?,?,?)",
                (person["id"], income, "renda diária: " + profession, day, year),
            )
        if expense:
            db.execute(
                "UPDATE citizens SET money=money-? WHERE id=?",
                (expense, person["id"]),
            )
            db.execute(
                "INSERT INTO economy_transactions(citizen_id,amount,reason,day,year) "
                "VALUES(?,?,?,?,?)",
                (person["id"], -expense, "despesas básicas", day, year),
            )

        balance = db.execute(
            "SELECT money FROM citizens WHERE id=?", (person["id"],)
        ).fetchone()["money"]
        if balance < 0:
            db.execute(
                "UPDATE citizens SET mood=MAX(0.05,mood-0.015) WHERE id=?",
                (person["id"],),
            )


def _process_day(db, day: int, year: int):
    rng = random.Random(year * 1000 + day)
    _daily_economy(db, day, year)
    residents = db.execute(
        "SELECT id,name,age,age_days FROM citizens WHERE alive=1 ORDER BY id"
    ).fetchall()

    for person in residents:
        age_days = person["age_days"] + 1
        age = person["age"]
        if age_days >= 360:
            age += 1
            age_days = 0
        db.execute(
            "UPDATE citizens SET age=?,age_days=? WHERE id=?",
            (age, age_days, person["id"]),
        )

        if age >= 75:
            annual_risk = 0.015 if age < 85 else (0.06 if age < 95 else 0.18)
            daily_risk = 1 - (1 - annual_risk) ** (1 / 360)
            if rng.random() < daily_risk:
                db.execute("UPDATE citizens SET alive=0 WHERE id=?", (person["id"],))
                _event(
                    db, "Uma vida chega ao fim",
                    f"{person['name']} faleceu aos {age} anos. A história da cidade guarda sua passagem.",
                    day, year,
                )

    # Nascimentos são eventos raros e só podem ocorrer em vínculos adultos já existentes.
    pairs = db.execute(
        "SELECT r.source_id,r.target_id,a.name AS first_name,a.age AS first_age,"
        "a.home_x,a.home_y,b.name AS second_name,b.age AS second_age "
        "FROM relationships r "
        "JOIN citizens a ON a.id=r.source_id AND a.alive=1 "
        "JOIN citizens b ON b.id=r.target_id AND b.alive=1 "
        "WHERE r.relation='parceiro' AND a.is_player=0 AND b.is_player=0"
    ).fetchall()
    for pair in pairs:
        if not (20 <= pair["first_age"] <= 40 and 20 <= pair["second_age"] <= 40):
            continue
        existing_children = db.execute(
            "SELECT COUNT(*) FROM relationships WHERE "
            "((source_id=? OR target_id=?) OR (source_id=? OR target_id=?)) "
            "AND relation IN ('mãe/pai','filho/filha')",
            (pair["source_id"], pair["source_id"], pair["target_id"], pair["target_id"]),
        ).fetchone()[0]
        if existing_children >= 12 or rng.random() >= 0.0009:
            continue

        first_names = ["Sofia", "Theo", "Luna", "Noah", "Helena", "Gael", "Maya", "Davi"]
        name = rng.choice(first_names) + " " + pair["first_name"].split()[-1]
        cursor = db.execute(
            "INSERT INTO citizens(name,age,age_days,profession,bio,personality,x,y,home_x,home_y,work_x,work_y,"
            "core_values,goals,energy,hunger,mood,social_need,money) "
            "VALUES(?,0,0,'Criança',?,?,?,?,?,?,?,?,?,?,0.95,0.18,0.72,0.30,10)",
            (name, "Nasceu na Cidade Viva e terá sua própria história conforme crescer.",
             "curiosa, em formação", pair["home_x"], pair["home_y"],
             pair["home_x"], pair["home_y"], pair["home_x"], pair["home_y"],
             json.dumps(["Descoberta", "Vínculos"], ensure_ascii=False),
             json.dumps(["Aprender", "Fazer amizades"], ensure_ascii=False)),
        )
        child_id = cursor.lastrowid
        for parent_id in (pair["source_id"], pair["target_id"]):
            db.execute(
                "INSERT INTO relationships(source_id,target_id,relation,strength) VALUES(?,?,?,1.0)",
                (parent_id, child_id, "mãe/pai"),
            )
            db.execute(
                "INSERT INTO relationships(source_id,target_id,relation,strength) VALUES(?,?,?,1.0)",
                (child_id, parent_id, "filho/filha"),
            )
        _event(db, "Uma nova pessoa chega à cidade",
               f"{name} nasceu. Uma nova história começa para a família.",
               day, year)


@app.get("/api/health")
def health():
    with connect() as db:
        population = db.execute(
            "SELECT COUNT(*) FROM citizens WHERE alive=1 AND is_player=0"
        ).fetchone()[0]
    return {
        "status": "ok",
        "service": "cidade-viva",
        "version": app.version,
        "population": population,
        "llm": {"provider": "ollama", "model": OLLAMA_MODEL, "url": OLLAMA_URL},
    }


@app.get("/api/city")
def city():
    with connect() as db:
        world_row = db.execute("SELECT * FROM world WHERE id=1").fetchone()
        if not world_row:
            raise HTTPException(500, "Estado do mundo não inicializado")
        world = dict(world_row)
        world["population"] = db.execute(
            "SELECT COUNT(*) FROM citizens WHERE alive=1 AND is_player=0"
        ).fetchone()[0]
        world["total_people_ever"] = db.execute(
            "SELECT COUNT(*) FROM citizens WHERE is_player=0"
        ).fetchone()[0]
        return world


@app.get("/api/citizens")
def citizens():
    with connect() as db:
        rows = db.execute(
            "SELECT id,name,age,profession,bio,personality,x,y,is_player,alive,"
            "core_values,goals,energy,hunger,mood,social_need,money,current_activity "
            "FROM citizens WHERE alive=1 ORDER BY is_player DESC,id"
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["core_values"] = json.loads(item["core_values"] or "[]")
            item["goals"] = json.loads(item["goals"] or "[]")
            result.append(item)
        return result


@app.post("/api/player/move")
def move_player(body: MoveInput):
    with connect() as db:
        result = db.execute(
            "UPDATE citizens SET x=?,y=? WHERE is_player=1 AND alive=1",
            (body.x, body.y),
        )
        if result.rowcount == 0:
            raise HTTPException(404, "Avatar do jogador não encontrado")
    return {"x": body.x, "y": body.y, "saved": True}


@app.post("/api/tick")
def tick():
    with connect() as db:
        world = db.execute("SELECT day,hour,season,year FROM world WHERE id=1").fetchone()
        hour = (world["hour"] + 1) % 24
        day = world["day"]
        year = world["year"]
        if hour == 0:
            day += 1
            if day > 360:
                day = 1
                year += 1
            _process_day(db, day, year)
        seasons = ["Primavera", "Verão", "Outono", "Inverno"]
        season = seasons[min(3, (day - 1) // 90)]
        db.execute(
            "UPDATE world SET day=?,hour=?,season=?,year=? WHERE id=1",
            (day, hour, season, year),
        )
        _move_residents(db, hour)
        _advance_needs(db, hour, day, year)
        _social_life(db, hour, day, year)
        population = db.execute(
            "SELECT COUNT(*) FROM citizens WHERE alive=1 AND is_player=0"
        ).fetchone()[0]
        return {
            "day": day, "hour": hour, "season": season,
            "year": year, "population": population,
        }


@app.get("/api/events")
def events(limit: int = 12):
    limit = max(1, min(limit, 50))
    with connect() as db:
        rows = db.execute(
            "SELECT id,title,description,day,year,created_at FROM world_events "
            "ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]


@app.get("/api/economy")
def economy():
    with connect() as db:
        summary = db.execute(
            "SELECT COUNT(*) AS people,ROUND(SUM(money),2) AS total_wealth,"
            "ROUND(AVG(money),2) AS average_balance,"
            "SUM(CASE WHEN money<0 THEN 1 ELSE 0 END) AS in_debt "
            "FROM citizens WHERE alive=1 AND is_player=0"
        ).fetchone()
        recent = db.execute(
            "SELECT e.id,e.citizen_id,c.name,e.amount,e.reason,e.day,e.year "
            "FROM economy_transactions e JOIN citizens c ON c.id=e.citizen_id "
            "ORDER BY e.id DESC LIMIT 20"
        ).fetchall()
        return {"summary": dict(summary), "recent_transactions": [dict(row) for row in recent]}


@app.get("/api/citizens/{citizen_id}/economy")
def citizen_economy(citizen_id: int):
    with connect() as db:
        person = db.execute(
            "SELECT id,name,money FROM citizens WHERE id=?", (citizen_id,)
        ).fetchone()
        if not person:
            raise HTTPException(404, "Habitante não encontrado")
        transactions = db.execute(
            "SELECT amount,reason,day,year,created_at FROM economy_transactions "
            "WHERE citizen_id=? ORDER BY id DESC LIMIT 40", (citizen_id,)
        ).fetchall()
        return {"citizen": dict(person), "transactions": [dict(row) for row in transactions]}


@app.get("/api/relationships")
def relationships():
    with connect() as db:
        rows = db.execute(
            "SELECT r.id,r.source_id,r.target_id,r.relation,r.strength,"
            "a.name AS source_name,b.name AS target_name "
            "FROM relationships r "
            "JOIN citizens a ON a.id=r.source_id "
            "JOIN citizens b ON b.id=r.target_id "
            "WHERE a.alive=1 AND b.alive=1 ORDER BY r.strength DESC"
        ).fetchall()
        return [dict(row) for row in rows]


@app.get("/api/citizens/{citizen_id}/family")
def citizen_family(citizen_id: int):
    with connect() as db:
        person = db.execute(
            "SELECT id,name,age,profession,alive FROM citizens WHERE id=?",
            (citizen_id,),
        ).fetchone()
        if not person:
            raise HTTPException(404, "Habitante não encontrado")

        parents = db.execute(
            "SELECT c.id,c.name,c.age,c.profession,c.alive FROM relationships r "
            "JOIN citizens c ON c.id=r.target_id "
            "WHERE r.source_id=? AND r.relation='filho/filha' ORDER BY c.name",
            (citizen_id,),
        ).fetchall()
        children = db.execute(
            "SELECT c.id,c.name,c.age,c.profession,c.alive FROM relationships r "
            "JOIN citizens c ON c.id=r.target_id "
            "WHERE r.source_id=? AND r.relation='mãe/pai' ORDER BY c.name",
            (citizen_id,),
        ).fetchall()
        partners = db.execute(
            "SELECT DISTINCT c.id,c.name,c.age,c.profession,c.alive FROM relationships r "
            "JOIN citizens c ON c.id=CASE WHEN r.source_id=? THEN r.target_id ELSE r.source_id END "
            "WHERE (r.source_id=? OR r.target_id=?) AND r.relation='parceiro' ORDER BY c.name",
            (citizen_id, citizen_id, citizen_id),
        ).fetchall()
        siblings = db.execute(
            "WITH parent_ids AS ("
            " SELECT target_id AS parent_id FROM relationships "
            " WHERE source_id=? AND relation='filho/filha'"
            ") "
            "SELECT DISTINCT c.id,c.name,c.age,c.profession,c.alive "
            "FROM relationships r JOIN parent_ids p ON p.parent_id=r.source_id "
            "JOIN citizens c ON c.id=r.target_id "
            "WHERE r.relation='mãe/pai' AND c.id<>? ORDER BY c.name",
            (citizen_id, citizen_id),
        ).fetchall()

        return {
            "person": dict(person),
            "parents": [dict(row) for row in parents],
            "partners": [dict(row) for row in partners],
            "children": [dict(row) for row in children],
            "siblings": [dict(row) for row in siblings],
        }


@app.get("/api/citizens/{citizen_id}/memories")
def citizen_memories(citizen_id: int, limit: int = 12):
    limit = max(1, min(limit, 40))
    with connect() as db:
        person = db.execute("SELECT id FROM citizens WHERE id=?", (citizen_id,)).fetchone()
        if not person:
            raise HTTPException(404, "Habitante não encontrado")
        rows = db.execute(
            "SELECT summary,importance,created_at FROM agent_memories "
            "WHERE citizen_id=? ORDER BY importance DESC,id DESC LIMIT ?",
            (citizen_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]


@app.get("/api/social/recent")
def recent_social(limit: int = 20):
    limit = max(1, min(limit, 50))
    with connect() as db:
        rows = db.execute(
            "SELECT s.id,a.name AS first_name,b.name AS second_name,s.summary,"
            "s.day,s.year,s.hour FROM social_interactions s "
            "JOIN citizens a ON a.id=s.source_id JOIN citizens b ON b.id=s.target_id "
            "ORDER BY s.id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]


@app.get("/api/citizens/{citizen_id}/history")
def history(citizen_id: int):
    with connect() as db:
        person = db.execute("SELECT id FROM citizens WHERE id=?", (citizen_id,)).fetchone()
        if not person:
            raise HTTPException(404, "Habitante não encontrado")
        rows = db.execute(
            "SELECT speaker,message,created_at FROM conversations "
            "WHERE citizen_id=? ORDER BY id DESC LIMIT 40", (citizen_id,)
        ).fetchall()
        return [dict(row) for row in reversed(rows)]


@app.post("/api/citizens/{citizen_id}/chat")
async def chat(citizen_id: int, body: ChatInput):
    message = body.message.strip()
    if not message:
        raise HTTPException(400, "Mensagem vazia")
    with connect() as db:
        person = db.execute(
            "SELECT * FROM citizens WHERE id=? AND alive=1", (citizen_id,)
        ).fetchone()
        if not person:
            raise HTTPException(404, "Habitante não encontrado")
        db.execute(
            "INSERT INTO conversations(citizen_id,speaker,message) VALUES(?,?,?)",
            (citizen_id, "Você", message),
        )
        prior = db.execute(
            "SELECT speaker,message FROM conversations WHERE citizen_id=? "
            "ORDER BY id DESC LIMIT 8", (citizen_id,),
        ).fetchall()
        memories = db.execute(
            "SELECT summary FROM agent_memories WHERE citizen_id=? "
            "ORDER BY importance DESC,id DESC LIMIT 8", (citizen_id,),
        ).fetchall()
        social_links = db.execute(
            "SELECT c.name,r.relation,r.strength FROM relationships r "
            "JOIN citizens c ON c.id=r.target_id "
            "WHERE r.source_id=? AND c.alive=1 ORDER BY r.strength DESC LIMIT 8",
            (citizen_id,),
        ).fetchall()

    core_values = json.loads(person["core_values"] or "[]")
    goals = json.loads(person["goals"] or "[]")
    relationship_context = ", ".join(
        "{} ({})".format(row["name"], row["relation"]) for row in social_links
    )
    memory_context = "; ".join(row["summary"] for row in memories)
    system = (
        f"Interprete a personagem fictícia {person['name']}, {person['age']} anos. "
        f"Profissão: {person['profession']}. Biografia: {person['bio']} "
        f"Personalidade: {person['personality']}. "
        f"Valores centrais: {', '.join(core_values)}. Objetivos pessoais: {', '.join(goals)}. "
        f"Estado atual: humor {person['mood']:.2f}/1, energia {person['energy']:.2f}/1, "
        f"fome {person['hunger']:.2f}/1, necessidade social {person['social_need']:.2f}/1, "
        f"dinheiro disponível {person['money']:.2f}. "
        f"Atividade atual: {person['current_activity']}. "
        f"Relações conhecidas: {relationship_context}. "
        f"Lembranças importantes: {memory_context}. "
        "Use lembranças e relações como contexto persistente, sem inventar fatos. "
        "Deixe que objetivos, valores e estado atual influenciem naturalmente suas respostas. "
        "Fale em português brasileiro, com voz própria e coerente com a biografia. "
        "Não diga que é uma pessoa real e não invente lembranças compartilhadas. "
        "Considere somente o histórico fornecido para lembrar conversas anteriores."
    )
    messages = [{"role": "system", "content": system}]
    for item in reversed(prior):
        role = "user" if item["speaker"] == "Você" else "assistant"
        messages.append({"role": role, "content": item["message"]})

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(240.0, connect=5.0)) as client:
            response = await client.post(
                OLLAMA_URL + "/v1/chat/completions",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False,
                    "temperature": 0.75,
                    "options": {"num_ctx": OLLAMA_NUM_CTX, "num_predict": 384},
                },
            )
            response.raise_for_status()
            answer = response.json()["choices"][0]["message"]["content"].strip()
            if not answer:
                raise ValueError("O modelo retornou uma resposta vazia")
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise HTTPException(
            503,
            "O modelo local não respondeu. Verifique se o Ollama está ligado e se "
            f"o modelo {OLLAMA_MODEL} está disponível.",
        ) from exc

    with connect() as db:
        db.execute(
            "INSERT INTO conversations(citizen_id,speaker,message) VALUES(?,?,?)",
            (citizen_id, person["name"], answer),
        )
        player = db.execute(
            "SELECT id,name FROM citizens WHERE is_player=1 AND alive=1 LIMIT 1"
        ).fetchone()
        if player and player["id"] != citizen_id:
            for source_id, target_id in ((citizen_id, player["id"]), (player["id"], citizen_id)):
                link = db.execute(
                    "SELECT id,strength FROM relationships WHERE source_id=? AND target_id=? "
                    "AND relation IN ('conhecido','amizade') ORDER BY strength DESC LIMIT 1",
                    (source_id, target_id),
                ).fetchone()
                if link:
                    new_strength = min(0.95, float(link["strength"]) + 0.06)
                    current_relation = db.execute(
                        "SELECT relation FROM relationships WHERE id=?", (link["id"],)
                    ).fetchone()["relation"]
                    new_relation = "amizade" if new_strength >= 0.62 else current_relation
                    db.execute(
                        "UPDATE relationships SET strength=?,relation=? WHERE id=?",
                        (new_strength, new_relation, link["id"]),
                    )
                else:
                    db.execute(
                        "INSERT OR IGNORE INTO relationships(source_id,target_id,relation,strength) "
                        "VALUES(?,?,'conhecido',0.36)",
                        (source_id, target_id),
                    )
            db.execute(
                "INSERT INTO agent_memories(citizen_id,event_id,summary,importance) VALUES(?,NULL,?,0.58)",
                (citizen_id, f"Conversou com {player['name']}: {message[:150]}"),
            )
            db.execute(
                "INSERT INTO agent_memories(citizen_id,event_id,summary,importance) VALUES(?,NULL,?,0.58)",
                (player["id"], f"Conversou com {person['name']}: {answer[:150]}"),
            )
            for memory_owner in (citizen_id, player["id"]):
                db.execute(
                    "DELETE FROM agent_memories WHERE citizen_id=? AND id NOT IN "
                    "(SELECT id FROM agent_memories WHERE citizen_id=? ORDER BY id DESC LIMIT 30)",
                    (memory_owner, memory_owner),
                )
    return {"citizen": person["name"], "answer": answer}


@app.get("/api/experiments")
def list_experiments():
    with connect() as db:
        rows = db.execute("SELECT * FROM experiments ORDER BY id DESC").fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["assumptions"] = json.loads(item["assumptions"] or "[]")
            result.append(item)
        return result


@app.post("/api/experiments")
def create_experiment(body: ExperimentInput):
    with connect() as db:
        cursor = db.execute(
            "INSERT INTO experiments(title,question,assumptions) VALUES(?,?,?)",
            (body.title.strip(), body.question.strip(),
             json.dumps(body.assumptions, ensure_ascii=False)),
        )
        experiment_id = cursor.lastrowid
        world = db.execute("SELECT day,year FROM world WHERE id=1").fetchone()
        _event(
            db, "Novo experimento criado",
            f"O cenário “{body.title.strip()}” foi registrado para análise.",
            world["day"], world["year"],
        )
        return {"id": experiment_id, "status": "draft", "title": body.title.strip()}


def _clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _initial_opinion(person: Any, experiment: Any, rng: random.Random) -> float:
    text = (experiment["question"] + " " + experiment["assumptions"]).lower()
    personality = person["personality"].lower()
    profession = person["profession"].lower()
    values = json.loads(person["core_values"] or "[]")
    goals = json.loads(person["goals"] or "[]")
    money = float(person["money"])
    score = rng.uniform(-0.34, 0.34)

    risk_terms = (
        "risco", "perigo", "custo", "prejuízo", "dívida", "incerteza",
        "perda", "orçamento", "imposto", "tributo", "taxa", "financiamento"
    )
    benefit_terms = (
        "saúde", "educação", "emprego", "ciência", "comunidade",
        "ambiente", "acesso", "transporte", "aprendizagem"
    )
    tradeoff_terms = ("limitado", "limitada", "escasso", "escassez", "sem verba")
    if any(term in text for term in risk_terms):
        score -= 0.22 if any(t in personality for t in ("cuidadosa", "desconfiado", "prático")) else 0.09
    if any(term in text for term in benefit_terms):
        score += 0.18 if any(t in personality for t in ("empática", "idealista", "curioso", "inventiva")) else 0.08
    if any(term in text for term in tradeoff_terms):
        score -= 0.18

    if "Conhecimento" in values and any(t in text for t in ("educação", "ciência", "pesquisa", "tecnologia")):
        score += 0.12
    if "Cuidado" in values and any(t in text for t in ("saúde", "família", "comunidade", "assistência")):
        score += 0.12
    if "Autonomia" in values and any(t in text for t in ("negócio", "empreendimento", "investimento", "autonomia")):
        score += 0.10
    if money < 20 and any(t in text for t in risk_terms):
        score -= 0.14
    if any(goal.lower().split()[0] in text for goal in goals if goal):
        score += 0.08

    role_context = {
        "médica": ("saúde", "medicina", "tratamento", "hospital"),
        "físico teórico": ("ciência", "pesquisa", "universo", "tecnologia"),
        "pesquisador": ("ciência", "pesquisa", "ambiente", "biodiversidade"),
        "engenheira": ("infraestrutura", "energia", "tecnologia", "construção"),
        "comerciante": ("empresa", "negócio", "investimento", "comércio", "preço"),
        "agricultor": ("agricultura", "alimento", "ambiente", "produção"),
        "professor": ("educação", "escola", "aprendizagem", "conhecimento"),
        "assistente social": ("comunidade", "acesso", "família", "desigualdade"),
        "artista": ("cultura", "arte", "criatividade", "educação"),
    }
    for key, terms in role_context.items():
        if key in profession and any(term in text for term in terms):
            score += 0.32
            break

    if "analítico" in personality or "metódica" in personality:
        score += 0.08
    if "ambicioso" in personality or "independente" in personality:
        score += 0.12
    if "tradicional" in personality or "reservado" in personality:
        score -= 0.09
    if "curioso" in personality or "inventiva" in personality:
        score += 0.10
    if "desconfiado" in personality:
        score -= 0.14

    return _clamp(score)


@app.post("/api/experiments/{experiment_id}/simulate")
def simulate_experiment(experiment_id: int):
    with connect() as db:
        experiment = db.execute(
            "SELECT * FROM experiments WHERE id=?", (experiment_id,)
        ).fetchone()
        if not experiment:
            raise HTTPException(404, "Experimento não encontrado")
        people = db.execute(
            "SELECT id,name,age,profession,bio,personality,core_values,goals,money "
            "FROM citizens WHERE alive=1 AND is_player=0 ORDER BY id"
        ).fetchall()
        if not people:
            raise HTTPException(409, "Não há habitantes ativos para simular")
        cursor = db.execute(
            "INSERT INTO simulation_runs(experiment_id,rounds) VALUES(?,3)",
            (experiment_id,),
        )
        run_id = cursor.lastrowid
        rng = random.Random(experiment_id * 7919 + run_id * 104729)
        stances = {
            person["id"]: _initial_opinion(
                person,
                {**dict(experiment), "assumptions": " ".join(json.loads(experiment["assumptions"] or "[]"))},
                rng,
            )
            for person in people
        }
        initial = dict(stances)
        edges = db.execute(
            "SELECT source_id,target_id,strength FROM relationships"
        ).fetchall()
        adjacency: dict[int, list[tuple[int, float]]] = {p["id"]: [] for p in people}
        for edge in edges:
            if edge["source_id"] in adjacency and edge["target_id"] in adjacency:
                adjacency[edge["source_id"]].append((edge["target_id"], edge["strength"]))
                adjacency[edge["target_id"]].append((edge["source_id"], edge["strength"]))

        for round_number in range(1, 4):
            updated = {}
            for person in people:
                neighbors = adjacency[person["id"]]
                valid = [(stances[other], weight) for other, weight in neighbors if weight > 0]
                if valid:
                    total_weight = sum(weight for _, weight in valid)
                    social_mean = sum(value * weight for value, weight in valid) / total_weight
                    updated[person["id"]] = _clamp(stances[person["id"]] * 0.82 + social_mean * 0.18)
                    most_influential = max(neighbors, key=lambda item: item[1])[0]
                    db.execute(
                        "INSERT INTO simulation_messages(run_id,source_id,target_id,round_number,summary) "
                        "VALUES(?,?,?,?,?)",
                        (run_id, most_influential, person["id"], round_number,
                         "A opinião foi ponderada pela relação social e pela posição inicial."),
                    )
                else:
                    updated[person["id"]] = stances[person["id"]]
            stances = updated

        for person in people:
            stance = stances[person["id"]]
            if stance > 0.14:
                rationale = "Mostra inclinação favorável, considerando seu perfil e o contexto apresentado."
            elif stance < -0.14:
                rationale = "Demonstra cautela ou resistência diante de aspectos do cenário."
            else:
                rationale = "Permanece em posição intermediária; faltam elementos para uma conclusão firme."
            db.execute(
                "INSERT INTO simulation_agents(run_id,citizen_id,initial_stance,final_stance,rationale) "
                "VALUES(?,?,?,?,?)",
                (run_id, person["id"], initial[person["id"]], stance, rationale),
            )
        db.execute("UPDATE experiments SET status='simulated' WHERE id=?", (experiment_id,))
        world = db.execute("SELECT day,year FROM world WHERE id=1").fetchone()
        _event(
            db, "Experimento concluído",
            f"A simulação “{experiment['title']}” concluiu três rodadas de interação.",
            world["day"], world["year"],
        )
        return _experiment_results(db, experiment_id, run_id)


def _experiment_results(db, experiment_id: int, run_id: int | None = None):
    experiment = db.execute(
        "SELECT id,title,question FROM experiments WHERE id=?", (experiment_id,)
    ).fetchone()
    if not experiment:
        raise HTTPException(404, "Experimento não encontrado")
    if run_id is None:
        last = db.execute(
            "SELECT id,rounds,created_at FROM simulation_runs "
            "WHERE experiment_id=? ORDER BY id DESC LIMIT 1", (experiment_id,)
        ).fetchone()
    else:
        last = db.execute(
            "SELECT id,rounds,created_at FROM simulation_runs WHERE id=? AND experiment_id=?",
            (run_id, experiment_id),
        ).fetchone()
    if not last:
        return {"experiment": dict(experiment), "run": None, "summary": None, "agents": []}

    rows = db.execute(
        "SELECT c.id,c.name,c.age,c.profession,sa.initial_stance,sa.final_stance,sa.rationale "
        "FROM simulation_agents sa JOIN citizens c ON c.id=sa.citizen_id "
        "WHERE sa.run_id=? ORDER BY sa.final_stance DESC",
        (last["id"],),
    ).fetchall()
    agents = []
    for row in rows:
        item = dict(row)
        item["position"] = (
            "favorável" if item["final_stance"] > 0.14 else
            "cautelosa" if item["final_stance"] < -0.14 else "indefinida"
        )
        agents.append(item)
    favorable = sum(a["position"] == "favorável" for a in agents)
    cautious = sum(a["position"] == "cautelosa" for a in agents)
    neutral = len(agents) - favorable - cautious
    return {
        "experiment": dict(experiment),
        "run": dict(last),
        "summary": {
            "population": len(agents),
            "favorable": favorable,
            "cautious": cautious,
            "neutral": neutral,
            "rounds": last["rounds"],
            "interpretation": "Resultado exploratório de agentes fictícios; não é previsão nem pesquisa representativa.",
        },
        "agents": agents,
    }


@app.get("/api/experiments/{experiment_id}/results")
def experiment_results(experiment_id: int):
    with connect() as db:
        return _experiment_results(db, experiment_id)


@app.get("/api/experiments/{experiment_id}/graph")
def experiment_graph(experiment_id: int):
    with connect() as db:
        exists = db.execute("SELECT id FROM experiments WHERE id=?", (experiment_id,)).fetchone()
        if not exists:
            raise HTTPException(404, "Experimento não encontrado")
        nodes = db.execute(
            "SELECT id,label,kind,description FROM knowledge_nodes WHERE experiment_id=?",
            (experiment_id,),
        ).fetchall()
        edges = db.execute(
            "SELECT id,source_id,target_id,relation,weight FROM knowledge_edges WHERE experiment_id=?",
            (experiment_id,),
        ).fetchall()
        return {"nodes": [dict(row) for row in nodes], "edges": [dict(row) for row in edges]}
