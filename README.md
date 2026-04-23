# Synapse - Backend

API REST da plataforma Synapse, responsavel por autenticacao, geracao de quizzes via LLM e sessoes simples de estudo com correcao deterministica.

## Funcionalidades

- Autenticacao com registro, login e protecao de rotas via JWT
- Geracao de quiz via `quiz_agent` a partir de uma transcricao
- Consulta de quizzes do usuario autenticado
- Sessoes de estudo com registro de respostas, score e historico
- Explicacoes por alternativa em cada flashcard

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Framework | FastAPI |
| Linguagem | Python 3.11+ |
| Banco de dados | PostgreSQL 15 |
| ORM | SQLAlchemy (`create_all` no startup) |
| LLM | OpenAI via Agno |
| Transcricao | SubTubly API |
| Autenticacao | JWT com `python-jose` + `passlib` |
| Containerizacao | Docker + Docker Compose |

## Estrutura

```text
app/
|- core/         # config, database, security
|- models/       # User, Video, Quiz, Flashcard, StudySession, SessionAnswer
|- schemas/      # request/response
|- routers/      # auth, quiz, sessions
|- services/     # subtubly.py, quiz_agent.py
\- dependencies.py
```

## Como rodar

```bash
cp .env.example .env
# preencha as variaveis no .env

docker compose up --build
```

A API sobe em `http://localhost:8000`. Documentacao interativa em `/docs`.
