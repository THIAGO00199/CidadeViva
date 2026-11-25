import json
import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.getenv("CIDADE_VIVA_DB", str(Path(__file__).parents[1] / "data" / "cidade_viva.db")))

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db

def _ensure_column(db, table: str, column: str, definition: str):
    columns = {row["name"] for row in db.execute(f"PRAGMA table_info({table})")}
    if column not in columns:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

def init_db():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS citizens (
          id INTEGER PRIMARY KEY, name TEXT NOT NULL, age INTEGER NOT NULL,
          profession TEXT NOT NULL, bio TEXT NOT NULL, personality TEXT NOT NULL,
          x REAL NOT NULL, y REAL NOT NULL, is_player INTEGER DEFAULT 0,
          memory TEXT DEFAULT '[]', alive INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS world (
          id INTEGER PRIMARY KEY CHECK (id=1), day INTEGER NOT NULL,
          hour INTEGER NOT NULL, season TEXT NOT NULL, year INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS conversations (
          id INTEGER PRIMARY KEY, citizen_id INTEGER NOT NULL,
          speaker TEXT NOT NULL, message TEXT NOT NULL,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS relationships (
          id INTEGER PRIMARY KEY, source_id INTEGER NOT NULL, target_id INTEGER NOT NULL,
          relation TEXT NOT NULL, strength REAL DEFAULT 0.5,
          UNIQUE(source_id, target_id, relation)
        );
        CREATE TABLE IF NOT EXISTS world_events (
          id INTEGER PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL,
          day INTEGER NOT NULL, year INTEGER NOT NULL,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS experiments (
          id INTEGER PRIMARY KEY, title TEXT NOT NULL, question TEXT NOT NULL,
          status TEXT DEFAULT 'draft', assumptions TEXT DEFAULT '[]',
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS knowledge_nodes (
          id INTEGER PRIMARY KEY, experiment_id INTEGER, label TEXT NOT NULL,
          kind TEXT NOT NULL, description TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS knowledge_edges (
          id INTEGER PRIMARY KEY, experiment_id INTEGER, source_id INTEGER NOT NULL,
          target_id INTEGER NOT NULL, relation TEXT NOT NULL, weight REAL DEFAULT 1.0
        );
        CREATE TABLE IF NOT EXISTS agent_memories (
          id INTEGER PRIMARY KEY, citizen_id INTEGER NOT NULL, event_id INTEGER,
          summary TEXT NOT NULL, importance REAL DEFAULT 0.5,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS economy_transactions (
          id INTEGER PRIMARY KEY, citizen_id INTEGER NOT NULL,
          amount REAL NOT NULL, reason TEXT NOT NULL,
          day INTEGER NOT NULL, year INTEGER NOT NULL,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS simulation_runs (
          id INTEGER PRIMARY KEY, experiment_id INTEGER NOT NULL,
          rounds INTEGER NOT NULL DEFAULT 3,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS simulation_agents (
          id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL, citizen_id INTEGER NOT NULL,
          initial_stance REAL NOT NULL, final_stance REAL NOT NULL, rationale TEXT NOT NULL,
          UNIQUE(run_id, citizen_id)
        );
        CREATE TABLE IF NOT EXISTS simulation_messages (
          id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL,
          source_id INTEGER NOT NULL, target_id INTEGER NOT NULL,
          round_number INTEGER NOT NULL, summary TEXT NOT NULL
        );
        INSERT OR IGNORE INTO world(id,day,hour,season,year)
          VALUES(1,1,8,'Primavera',1);
        """)

        _ensure_column(db, "citizens", "age_days", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(db, "citizens", "home_x", "REAL")
        _ensure_column(db, "citizens", "home_y", "REAL")
        _ensure_column(db, "citizens", "work_x", "REAL")
        _ensure_column(db, "citizens", "work_y", "REAL")
        _ensure_column(db, "citizens", "core_values", "TEXT NOT NULL DEFAULT '[]'")
        _ensure_column(db, "citizens", "goals", "TEXT NOT NULL DEFAULT '[]'")
        _ensure_column(db, "citizens", "energy", "REAL NOT NULL DEFAULT 0.85")
        _ensure_column(db, "citizens", "hunger", "REAL NOT NULL DEFAULT 0.20")
        _ensure_column(db, "citizens", "mood", "REAL NOT NULL DEFAULT 0.65")
        _ensure_column(db, "citizens", "social_need", "REAL NOT NULL DEFAULT 0.35")
        _ensure_column(db, "citizens", "money", "REAL NOT NULL DEFAULT 100.0")
        _ensure_column(db, "citizens", "current_activity", "TEXT NOT NULL DEFAULT 'Em casa'")
        db.execute("""
          CREATE TABLE IF NOT EXISTS social_interactions (
            id INTEGER PRIMARY KEY,
            source_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            day INTEGER NOT NULL,
            year INTEGER NOT NULL,
            hour INTEGER NOT NULL,
            summary TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
          )
        """)
        db.execute(
            "DELETE FROM relationships WHERE id NOT IN "
            "(SELECT MIN(id) FROM relationships GROUP BY source_id,target_id,relation)"
        )
        db.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_relationship_unique "
            "ON relationships(source_id,target_id,relation)"
        )

        if db.execute("SELECT COUNT(*) FROM citizens").fetchone()[0] == 0:
            seed = [
              ("Henrique Martins",42,"Físico teórico","Pesquisa fundamentos da matéria e do universo.","analítico, curioso, reservado"),
              ("Lia Ferreira",34,"Médica","Trabalha na unidade de saúde do bairro.","cuidadosa, prática, empática"),
              ("Ravi Nascimento",29,"Professor","Ensina história e filosofia.","questionador, paciente, comunicativo"),
              ("Marta Oliveira",67,"Aposentada","Conhece a história de muitas famílias da cidade.","observadora, afetuosa, tradicional"),
              ("Caio Mendes",21,"Estudante","Estuda tecnologia e procura estágio.","curioso, sociável, ambicioso"),
              ("Joana Costa",38,"Comerciante","Administra uma pequena mercearia.","pragmática, organizada, falante"),
              ("Samuel Rocha",51,"Agricultor","Produz alimentos em uma propriedade familiar.","trabalhador, paciente, independente"),
              ("Amina Yusuf",31,"Engenheira","Trabalha com infraestrutura e energia.","metódica, inventiva, direta"),
              ("Bento Alves",74,"Monge","Dedica-se à contemplação e ao serviço comunitário.","sereno, reflexivo, discreto"),
              ("Nina Barros",16,"Estudante","Está no ensino médio e gosta de música.","expressiva, curiosa, sociável"),
              ("Davi Lima",45,"Motorista","Conhece rotas e pessoas de toda a região.","bem-humorado, prático, observador"),
              ("Elisa Prado",27,"Artista","Produz ilustrações e dá oficinas.","criativa, sensível, independente"),
              ("Pedro Santos",39,"Pedreiro","Trabalha em obras e reformas.","prático, leal, reservado"),
              ("Rosa Almeida",58,"Cozinheira","Prepara refeições para eventos locais.","acolhedora, habilidosa, comunicativa"),
              ("Miguel Reis",33,"Pesquisador","Estuda ecologia e biodiversidade.","analítico, paciente, idealista"),
              ("Lourdes Silva",49,"Costureira","Mantém um pequeno ateliê.","detalhista, persistente, gentil"),
              ("André Pires",24,"Desempregado","Procura oportunidades e ajuda a família.","resiliente, desconfiado, observador"),
              ("Clara Monteiro",12,"Estudante","Gosta de animais e ciências naturais.","curiosa, imaginativa, espontânea"),
              ("Elias Cardoso",63,"Pessoa em situação de rua","Tem uma trajetória de vida complexa e vínculos na cidade.","experiente, reservado, atento"),
              ("Tereza Gomes",36,"Assistente social","Atua com famílias e serviços comunitários.","empática, firme, colaborativa")
            ]
            for i, row in enumerate(seed):
                x, y = 8 + (i % 5) * 5, 8 + (i // 5) * 6
                cursor = db.execute(
                    "INSERT INTO citizens(name,age,profession,bio,personality,x,y,home_x,home_y,work_x,work_y) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (*row, x, y, x, y, 12 + (i % 6) * 4, 10 + (i % 3) * 4)
                )
            db.execute(
                "INSERT INTO citizens(name,age,profession,bio,personality,x,y,is_player,home_x,home_y,work_x,work_y) "
                "VALUES(?,?,?,?,?,?,?,1,?,?,?,?)",
                ("Seu personagem",17,"Visitante","Avatar do jogador, personalizável.","curioso, explorador",15,15,15,15,15,15)
            )

        db.execute("UPDATE citizens SET home_x=x WHERE home_x IS NULL")
        db.execute("UPDATE citizens SET home_y=y WHERE home_y IS NULL")
        db.execute("UPDATE citizens SET work_x=x, work_y=y WHERE work_x IS NULL OR work_y IS NULL")

        goals_by_job = {
            "Físico teórico": ["Investigar questões fundamentais", "Compartilhar descobertas"],
            "Médica": ["Cuidar dos pacientes", "Aprimorar o atendimento de saúde"],
            "Professor": ["Ensinar com qualidade", "Estimular a curiosidade dos alunos"],
            "Aposentada": ["Manter vínculos com a comunidade", "Compartilhar experiências"],
            "Estudante": ["Aprender coisas novas", "Construir seu próprio caminho"],
            "Comerciante": ["Manter o negócio sustentável", "Atender bem a vizinhança"],
            "Agricultor": ["Produzir alimentos", "Cuidar da propriedade"],
            "Engenheira": ["Resolver problemas técnicos", "Melhorar a infraestrutura"],
            "Monge": ["Praticar contemplação", "Servir à comunidade"],
            "Motorista": ["Trabalhar com segurança", "Conhecer novos caminhos"],
            "Artista": ["Criar trabalhos autorais", "Compartilhar arte"],
            "Pedreiro": ["Entregar obras bem-feitas", "Garantir estabilidade"],
            "Cozinheira": ["Preparar boas refeições", "Valorizar a cultura local"],
            "Pesquisador": ["Investigar a natureza", "Divulgar conhecimento"],
            "Costureira": ["Aprimorar o ateliê", "Criar peças duráveis"],
            "Desempregado": ["Encontrar uma oportunidade", "Ajudar a família"],
            "Pessoa em situação de rua": ["Encontrar segurança e estabilidade", "Construir vínculos de confiança"],
            "Assistente social": ["Apoiar famílias", "Ampliar o acesso a serviços"],
            "Criança": ["Aprender", "Fazer amizades"],
            "Visitante": ["Explorar a cidade", "Conhecer seus moradores"],
        }
        initial_money = {
            "Pessoa em situação de rua": 12.0, "Desempregado": 35.0,
            "Aposentada": 120.0, "Estudante": 40.0, "Criança": 10.0,
            "Monge": 60.0, "Visitante": 100.0,
        }
        for citizen in db.execute(
            "SELECT id,profession,personality,core_values,goals,money FROM citizens"
        ).fetchall():
            if citizen["core_values"] == "[]" or citizen["goals"] == "[]":
                personality = citizen["personality"].lower()
                traits = [
                    ("analítico", "Conhecimento"), ("curioso", "Descoberta"),
                    ("empática", "Cuidado"), ("empático", "Cuidado"),
                    ("prático", "Pragmatismo"), ("independente", "Autonomia"),
                    ("tradicional", "Estabilidade"), ("idealista", "Impacto coletivo"),
                    ("ambicioso", "Realização"), ("criativa", "Expressão"),
                    ("reservado", "Privacidade"), ("sereno", "Equilíbrio"),
                    ("resiliente", "Resiliência"), ("questionador", "Pensamento crítico"),
                ]
                values = list(dict.fromkeys(
                    label for token, label in traits if token in personality
                )) or ["Convivência", "Estabilidade"]
                goals = goals_by_job.get(
                    citizen["profession"],
                    ["Desenvolver habilidades", "Manter relações significativas"],
                )
                starting_money = (
                    initial_money.get(citizen["profession"], 100.0)
                    if citizen["core_values"] == "[]" and citizen["goals"] == "[]"
                    else citizen["money"]
                )
                db.execute(
                    "UPDATE citizens SET core_values=?,goals=?,money=? WHERE id=?",
                    (json.dumps(values, ensure_ascii=False),
                     json.dumps(goals, ensure_ascii=False), starting_money, citizen["id"]),
                )

        if db.execute("SELECT COUNT(*) FROM relationships").fetchone()[0] == 0:
            ids = [row["id"] for row in db.execute(
                "SELECT id FROM citizens WHERE is_player=0 AND alive=1 ORDER BY id"
            )]
            # Laços iniciais representam convivência de bairro, não parentesco.
            for index, citizen_id in enumerate(ids):
                neighbor = ids[(index + 1) % len(ids)]
                db.execute(
                    "INSERT OR IGNORE INTO relationships(source_id,target_id,relation,strength) VALUES(?,?,?,?)",
                    (citizen_id, neighbor, "vizinho", 0.42)
                )
                if index + 3 < len(ids):
                    db.execute(
                        "INSERT OR IGNORE INTO relationships(source_id,target_id,relation,strength) VALUES(?,?,?,?)",
                        (citizen_id, ids[index + 3], "conhecido", 0.28)
                    )
            pairs = [(1, 6), (2, 11), (3, 15)]
            for first, second in pairs:
                db.execute(
                    "INSERT OR IGNORE INTO relationships(source_id,target_id,relation,strength) VALUES(?,?,?,?)",
                    (first, second, "amizade", 0.68)
                )

        # Vínculos iniciais entre adultos; os laços podem mudar durante a simulação.
        for first, second in [(2, 13), (5, 12)]:
            db.execute(
                "INSERT OR IGNORE INTO relationships(source_id,target_id,relation,strength) VALUES(?,?,?,?)",
                (first, second, "parceiro", 0.88)
            )

        if db.execute("SELECT COUNT(*) FROM world_events").fetchone()[0] == 0:
            db.execute(
                "INSERT INTO world_events(title,description,day,year) VALUES(?,?,1,1)",
                ("A cidade desperta", "Os primeiros moradores começam mais um dia na Cidade Viva.")
            )
