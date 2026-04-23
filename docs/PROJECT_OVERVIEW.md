# PROJECT OVERVIEW - SYNAPSE

## 1. Descricao Geral

Plataforma web voltada para estudos que transforma videos do YouTube em quizzes de aprendizado. O backend recebe uma transcricao, usa um agente LLM para gerar resumo e flashcards, e depois registra sessoes simples de resposta sem tutor agent.

## 2. Stack

| Camada | Tecnologia |
|---|---|
| Frontend | React + Vite + TailwindCSS |
| Backend | Python 3.11+ + FastAPI |
| Banco de dados | PostgreSQL |
| ORM | SQLAlchemy |
| LLM | Agno + OpenAI/Groq |
| API externa | SubTubly API |
| Autenticacao | JWT |
| Containerizacao | Docker + Docker Compose |

## 3. Fluxo Principal

### 3.1 Geracao de Quiz

1. Usuario autenticado envia a URL do video e a quantidade de perguntas desejada.
2. O backend obtem uma transcricao e chama o `quiz_agent`.
3. O `quiz_agent` retorna um JSON com `summary` e `flashcards`.
4. Cada flashcard contem `question`, `options`, `correct_answer` e `explanations`.
5. O backend salva quiz e flashcards e retorna o resultado completo.

### 3.2 Sessao de Estudo

1. Frontend inicia uma sessao com `POST /api/sessions`.
2. A cada resposta, `POST /api/sessions/{id}/answer` envia a alternativa escolhida.
3. O backend corrige localmente, salva a resposta e retorna:
   - `is_correct`
   - `correct_answer`
   - `selected_explanation`
   - `correct_explanation`
4. `POST /api/sessions/{id}/finish` calcula `score` e `total`.

## 4. Modelagem

### `flashcards`

```sql
id              UUID PRIMARY KEY
quiz_id         UUID REFERENCES quizzes(id)
question        TEXT NOT NULL
options         JSONB NOT NULL
correct_answer  INTEGER NOT NULL
explanations    JSONB NOT NULL
position        INTEGER
```

### `study_sessions`

```sql
id          UUID PRIMARY KEY
user_id     UUID REFERENCES users(id)
quiz_id     UUID REFERENCES quizzes(id)
score       INTEGER
total       INTEGER
started_at  TIMESTAMP
finished_at TIMESTAMP
```

### `session_answers`

```sql
id             UUID PRIMARY KEY
session_id     UUID REFERENCES study_sessions(id)
flashcard_id   UUID REFERENCES flashcards(id)
answer_given   INTEGER
is_correct     BOOLEAN
answered_at    TIMESTAMP
```

## 5. Endpoints

### Auth

```text
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
```

### Quiz

```text
POST /api/quiz/generate
GET  /api/quiz/{id}
GET  /api/quiz/
```

### Sessions

```text
POST /api/sessions
POST /api/sessions/{id}/answer
GET  /api/sessions/{id}
POST /api/sessions/{id}/finish
GET  /api/sessions/
```

## 6. Contrato do Quiz Agent

```json
{
  "summary": "Resumo do conteudo do video...",
  "flashcards": [
    {
      "question": "Qual e o conceito de X?",
      "options": ["Opcao A", "Opcao B", "Opcao C", "Opcao D"],
      "correct_answer": 2,
      "explanations": [
        "A opcao A esta incorreta porque...",
        "A opcao B esta incorreta porque...",
        "A opcao C esta correta porque...",
        "A opcao D esta incorreta porque..."
      ]
    }
  ]
}
```
