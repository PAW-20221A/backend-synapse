import json

from pydantic import BaseModel, ValidationError, model_validator

from app.core.config import settings

QUIZ_SYSTEM_PROMPT = """Voce e um especialista em criar materiais de estudo.
Dada uma transcricao de video, gere um resumo e um conjunto de flashcards no formato JSON abaixo.
Responda APENAS com o JSON, sem texto adicional.

Formato:
{
  "summary": "Resumo conciso do conteudo...",
  "flashcards": [
    {
      "question": "Pergunta sobre o conteudo?",
      "options": ["Opcao A", "Opcao B", "Opcao C", "Opcao D"],
      "correct_answer": 0,
      "explanations": [
        "Explicacao da Opcao A",
        "Explicacao da Opcao B",
        "Explicacao da Opcao C",
        "Explicacao da Opcao D"
      ]
    }
  ]
}
"""


class QuizAgentFlashcard(BaseModel):
    question: str
    options: list[str]
    correct_answer: int
    explanations: list[str]

    @model_validator(mode="after")
    def validate_structure(self) -> "QuizAgentFlashcard":
        if len(self.options) != len(self.explanations):
            raise ValueError("Flashcard explanations must align with options.")
        if not 0 <= self.correct_answer < len(self.options):
            raise ValueError("Flashcard correct_answer is out of range.")
        return self


class QuizAgentResponse(BaseModel):
    summary: str
    flashcards: list[QuizAgentFlashcard]


def validate_quiz_payload(payload: dict, question_count: int | None = None) -> dict:
    try:
        validated = QuizAgentResponse.model_validate(payload)
    except ValidationError as exc:
        raise ValueError("Invalid quiz payload returned by quiz agent.") from exc

    if question_count is not None and len(validated.flashcards) != question_count:
        raise ValueError("Quiz agent returned an unexpected number of flashcards.")

    return validated.model_dump()


async def generate_quiz_from_transcript(transcript: str, question_count: int) -> dict:
    """Uses the Agno Quiz Generator Agent to produce summary + flashcards."""
    from agno.agent import Agent
    from agno.models.openai import OpenAIChat

    agent = Agent(
        model=OpenAIChat(id="gpt-4o-mini", api_key=settings.openai_api_key),
        system_message=QUIZ_SYSTEM_PROMPT,
    )

    prompt = (
        f"Transcricao do video:\n\n{transcript}\n\n"
        f"Gere exatamente {question_count} flashcards com base nesta transcricao."
    )

    response = await agent.arun(prompt)

    content = response.content
    if isinstance(content, dict):
        payload = content
    elif isinstance(content, str):
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError("Quiz agent returned invalid JSON.") from exc
    else:
        raise ValueError("Quiz agent returned an unsupported content format.")

    return validate_quiz_payload(payload, question_count)
