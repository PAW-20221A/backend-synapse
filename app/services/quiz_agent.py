import json

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from app.core.config import settings

QUIZ_SYSTEM_PROMPT = """Você é um especialista em criar materiais de estudo.
Dado uma transcrição de vídeo, gere um resumo e um conjunto de flashcards no formato JSON abaixo.
Responda APENAS com o JSON, sem texto adicional.

Formato:
{
  "summary": "Resumo conciso do conteúdo...",
  "flashcards": [
    {
      "question": "Pergunta sobre o conteúdo?",
      "options": ["Opção A", "Opção B", "Opção C", "Opção D"],
      "correct_answer": 0,
      "explanation": "Explicação do por quê esta é a resposta correta..."
    }
  ]
}
"""


async def generate_quiz_from_transcript(transcript: str, question_count: int) -> dict:
    """Uses the Agno Quiz Generator Agent to produce summary + flashcards."""
    agent = Agent(
        model=OpenAIChat(id="gpt-4o-mini", api_key=settings.openai_api_key),
        system_prompt=QUIZ_SYSTEM_PROMPT,
    )

    prompt = (
        f"Transcrição do vídeo:\n\n{transcript}\n\n"
        f"Gere exatamente {question_count} flashcards com base nesta transcrição."
    )

    response = await agent.arun(prompt)
    return json.loads(response.content)
