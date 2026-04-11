# Synapse — Backend
#Estive aqui. Prof. Rondineli Seba Salomão
API REST da plataforma Synapse, responsável por autenticação, geração de quizzes via LLM e condução de sessões de estudo com agente tutor.

## Funcionalidades

- **Autenticação** — registro, login e proteção de rotas via JWT
- **Geração de quiz** — recebe uma URL do YouTube, obtém a transcrição via SubTubly API e aciona um agente LLM (Agno) para gerar resumo + flashcards
- **Cache de vídeos** — evita chamadas repetidas à SubTubly para o mesmo vídeo (chave: `youtube_id`)
- **Sessão de estudo** — agente tutor avalia cada resposta do usuário e retorna feedback personalizado
- **Histórico** — persiste sessões e scores por usuário

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Framework | FastAPI |
| Linguagem | Python 3.11+ |
| Banco de dados | PostgreSQL 15 |
| ORM | SQLAlchemy (create_all no startup) |
| Framework agêntico | Agno |
| LLM | OpenAI (gpt-4o-mini) |
| Transcrição | SubTubly API |
| Autenticação | JWT — python-jose + passlib[bcrypt] |
| Containerização | Docker + Docker Compose |

## Estrutura

```
app/
├── core/         # config, database, security (JWT)
├── models/       # ORM: User, Video, Quiz, Flashcard, StudySession, SessionAnswer
├── schemas/      # Pydantic: request/response
├── routers/      # auth, quiz, sessions
├── services/     # subtubly.py, quiz_agent.py, tutor_agent.py
└── dependencies.py  # get_db, get_current_user
```

## Como rodar

```bash
cp .env.example .env
# preencha as variáveis no .env

docker compose up --build
```

A API sobe em `http://localhost:8000`. Documentação interativa em `/docs`.
