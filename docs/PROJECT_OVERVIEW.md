# PROJECT OVERVIEW — SYNAPSE

> Documento de referência para geração de infraestrutura inicial via Claude Code.

---

## 1. Descrição Geral

Plataforma web voltada para estudos que transforma vídeos do YouTube em sessões interativas de aprendizado. O usuário cola um link de vídeo, e o sistema — usando uma API externa de transcrição e integração com LLMs — gera automaticamente um resumo e um conjunto de flashcards/quiz. Em seguida, um agente tutor conduz uma sessão interativa, fazendo as perguntas, avaliando as respostas e explicando os acertos e erros.

---

## 2. Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Frontend | React + Vite + TailwindCSS |
| Backend | Python 3.11+ + FastAPI |
| Banco de Dados | PostgreSQL |
| ORM | SQLAlchemy + Alembic (migrations) |
| Framework Agêntico | Agno |
| LLM | OpenAI ou Groq (via Agno) |
| API Externa | SubTubly API (transcrição de vídeos do YouTube) |
| Autenticação | JWT (python-jose + passlib) |
| Containerização | Docker + Docker Compose |
| CI/CD | GitHub Actions |

---

## 3. Arquitetura do Sistema

```
┌─────────────┐     HTTP      ┌──────────────────┐
│   React     │ ◄───────────► │   FastAPI        │
│  Frontend   │               │   Backend        │
└─────────────┘               └────────┬─────────┘
                                       │
              ┌────────────────────────┼──────────────────────┐
              │                        │                      │
              ▼                        ▼                      ▼
   ┌──────────────────┐    ┌───────────────────┐   ┌─────────────────┐
   │   SubTubly API   │    │   Agno Framework  │   │   PostgreSQL    │
   │  (transcrição)   │    │  (agente + LLM)   │   │   (banco local) │
   └──────────────────┘    └───────────────────┘   └─────────────────┘
```

---

## 4. Fluxo Principal da Aplicação

### 4.1 Geração de Quiz (fluxo síncrono)

1. Usuário autenticado cola a URL do YouTube e define o número de perguntas desejadas.
2. Frontend faz `POST /api/quiz/generate` com `{ url, question_count }`.
3. Backend verifica no banco se já existe quiz gerado para aquela URL (cache). Se sim, retorna direto.
4. Se não: chama a SubTubly API para obter a transcrição completa do vídeo.
5. Inicializa o agente Agno (Quiz Generator Agent) passando a transcrição e o número de perguntas.
6. O agente chama o LLM com um prompt estruturado e recebe um JSON com perguntas, alternativas e explicações.
7. O backend salva o quiz no banco (tabela `quizzes` + tabela `flashcards`) e retorna o objeto completo ao frontend.
8. Frontend exibe o resumo e redireciona para a sessão de estudo.

### 4.2 Sessão de Estudo (agente tutor)

1. Frontend carrega o quiz pelo ID e inicia uma sessão: `POST /api/sessions`.
2. O agente tutor recebe o conjunto de flashcards e o histórico da conversa.
3. A cada mensagem do usuário: `POST /api/sessions/{id}/answer` com a resposta escolhida.
4. O backend repassa ao agente tutor o estado atual (pergunta, resposta do usuário, histórico).
5. O agente chama o LLM e retorna feedback explicando o acerto ou o erro.
6. Ao final, a sessão é encerrada e o score é salvo no banco.

---

## 5. Modelagem do Banco de Dados

### Tabela: `users`
```sql
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
email         VARCHAR(255) UNIQUE NOT NULL
password_hash VARCHAR(255) NOT NULL
name          VARCHAR(255)
created_at    TIMESTAMP DEFAULT NOW()
```

### Tabela: `videos`
```sql
id             UUID PRIMARY KEY DEFAULT gen_random_uuid()
youtube_url    TEXT NOT NULL
youtube_id     VARCHAR(50) UNIQUE NOT NULL  -- extraído da URL, usado como cache key
title          TEXT
transcript     TEXT
language       VARCHAR(10) DEFAULT 'pt'
created_at     TIMESTAMP DEFAULT NOW()
```

### Tabela: `quizzes`
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
video_id    UUID REFERENCES videos(id)
user_id     UUID REFERENCES users(id)
summary     TEXT
created_at  TIMESTAMP DEFAULT NOW()
```

### Tabela: `flashcards`
```sql
id                  UUID PRIMARY KEY DEFAULT gen_random_uuid()
quiz_id             UUID REFERENCES quizzes(id)
question            TEXT NOT NULL
options             JSONB NOT NULL  -- array de strings com as alternativas
correct_answer      INTEGER NOT NULL  -- índice da alternativa correta
explanation         TEXT NOT NULL
position            INTEGER  -- ordem da pergunta no quiz
```

### Tabela: `study_sessions`
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id     UUID REFERENCES users(id)
quiz_id     UUID REFERENCES quizzes(id)
score       INTEGER  -- número de acertos
total       INTEGER  -- total de perguntas
started_at  TIMESTAMP DEFAULT NOW()
finished_at TIMESTAMP
```

### Tabela: `session_answers`
```sql
id             UUID PRIMARY KEY DEFAULT gen_random_uuid()
session_id     UUID REFERENCES study_sessions(id)
flashcard_id   UUID REFERENCES flashcards(id)
answer_given   INTEGER  -- índice da alternativa escolhida pelo usuário
is_correct     BOOLEAN
answered_at    TIMESTAMP DEFAULT NOW()
```

---

## 6. Endpoints da API (FastAPI)

### Auth
```
POST   /api/auth/register     -- cria conta
POST   /api/auth/login        -- retorna JWT
GET    /api/auth/me           -- dados do usuário autenticado
```

### Quiz
```
POST   /api/quiz/generate     -- submete URL + question_count, retorna quiz completo
GET    /api/quiz/{id}         -- busca quiz por ID
GET    /api/quiz/             -- lista quizzes do usuário autenticado
```

### Sessions
```
POST   /api/sessions                    -- inicia sessão para um quiz_id
POST   /api/sessions/{id}/answer        -- envia resposta de um flashcard, recebe feedback do agente
GET    /api/sessions/{id}               -- estado atual da sessão
POST   /api/sessions/{id}/finish        -- encerra sessão e salva score
GET    /api/sessions/                   -- histórico de sessões do usuário
```

---

## 7. Estrutura de Pastas do Projeto

```
[nome-do-projeto]/
├── backend/
│   ├── app/
│   │   ├── main.py                 # entrypoint FastAPI
│   │   ├── core/
│   │   │   ├── config.py           # variáveis de ambiente (pydantic-settings)
│   │   │   ├── security.py         # JWT utils
│   │   │   └── database.py         # engine + session SQLAlchemy
│   │   ├── models/                 # modelos SQLAlchemy (ORM)
│   │   │   ├── user.py
│   │   │   ├── video.py
│   │   │   ├── quiz.py
│   │   │   ├── flashcard.py
│   │   │   └── session.py
│   │   ├── schemas/                # schemas Pydantic (request/response)
│   │   │   ├── auth.py
│   │   │   ├── quiz.py
│   │   │   └── session.py
│   │   ├── routers/                # rotas FastAPI
│   │   │   ├── auth.py
│   │   │   ├── quiz.py
│   │   │   └── sessions.py
│   │   ├── services/               # lógica de negócio
│   │   │   ├── subtubly.py         # integração com SubTubly API
│   │   │   ├── quiz_agent.py       # Agno: Quiz Generator Agent
│   │   │   └── tutor_agent.py      # Agno: Tutor Agent
│   │   └── dependencies.py         # get_db, get_current_user
│   ├── alembic/                    # migrations
│   ├── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── Home.jsx            # input da URL
│   │   │   ├── Quiz.jsx            # exibe resumo e flashcards gerados
│   │   │   ├── Session.jsx         # sessão com o agente tutor
│   │   │   ├── History.jsx         # histórico do usuário
│   │   │   ├── Login.jsx
│   │   │   └── Register.jsx
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── FlashCard.jsx
│   │   │   ├── ChatBubble.jsx      # mensagens do agente tutor
│   │   │   └── LoadingState.jsx    # estado de "gerando quiz..."
│   │   ├── services/
│   │   │   └── api.js              # axios instance + chamadas à API
│   │   └── store/                  # context ou zustand para estado global
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
├── .github/
│   └── workflows/
│       └── ci.yml
└── README.md
```

---

## 8. Variáveis de Ambiente (.env.example)

```env
# Backend
DATABASE_URL=postgresql://postgres:postgres@db:5432/[nome_do_projeto]
SECRET_KEY=sua-chave-secreta-jwt
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# APIs externas
SUBTUBLY_API_URL=https://...
SUBTUBLY_API_KEY=...
OPENAI_API_KEY=...       # ou GROQ_API_KEY

# Frontend (Vite)
VITE_API_BASE_URL=http://localhost:8000
```

---

## 9. Docker Compose (estrutura esperada)

Três serviços principais:
- `db` — PostgreSQL 15, com volume persistente
- `backend` — FastAPI rodando com uvicorn na porta 8000
- `frontend` — Vite dev server na porta 5173 (ou build servido por nginx em produção)

---

## 10. Agentes LLM (Agno)

### Quiz Generator Agent
- **Quando é chamado:** uma vez, logo após receber a transcrição da SubTubly API
- **Input:** transcrição completa + número de perguntas desejadas
- **Output:** JSON estruturado com `summary` (string) e `flashcards` (array)
- **Formato esperado do JSON:**
```json
{
  "summary": "Resumo do conteúdo do vídeo...",
  "flashcards": [
    {
      "question": "Qual é o conceito de X?",
      "options": ["Opção A", "Opção B", "Opção C", "Opção D"],
      "correct_answer": 2,
      "explanation": "A opção C está correta porque..."
    }
  ]
}
```

### Tutor Agent
- **Quando é chamado:** a cada resposta do usuário durante a sessão de estudo
- **Input:** flashcard atual + resposta escolhida pelo usuário + histórico da conversa
- **Output:** mensagem de texto com feedback personalizado (acerto ou erro + explicação)
- **Comportamento esperado:** manter tom encorajador, reforçar o conteúdo correto, não apenas dizer "errado"

---

## 11. Ordem de Implementação Recomendada

1. Setup do repositório, Docker Compose e estrutura de pastas
2. Modelos SQLAlchemy + primeira migration com Alembic
3. Autenticação (register, login, JWT, middleware)
4. Integração com SubTubly API (serviço isolado, testável)
5. Quiz Generator Agent com Agno + LLM
6. Endpoints de quiz (generate, get, list)
7. Tutor Agent com Agno + histórico de conversa
8. Endpoints de sessão (start, answer, finish)
9. Frontend: autenticação + home + página de quiz
10. Frontend: página de sessão (chat com o tutor)
11. Frontend: histórico e dashboard
12. GitHub Actions CI (lint + testes básicos)

---

## 12. Observações Finais para o Claude Code

- Usar `pydantic-settings` para carregar variáveis de ambiente no backend
- Usar `python-jose` e `passlib[bcrypt]` para JWT e hash de senhas
- Todas as rotas protegidas devem usar `Depends(get_current_user)`
- O campo `options` dos flashcards deve ser `JSONB` no PostgreSQL e `list[str]` no schema Pydantic
- O `youtube_id` extraído da URL é a cache key: antes de chamar a SubTubly API, verificar se já existe um registro com aquele `youtube_id` no banco
- Migrations devem ser geradas com Alembic e nunca editadas manualmente após aplicadas
