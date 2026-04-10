from agno.agent import Agent
from agno.models.openai import OpenAIChat

from app.core.config import settings

TUTOR_SYSTEM_PROMPT = """Você é um tutor encorajador e paciente.
Seu trabalho é avaliar a resposta do aluno a uma pergunta de múltipla escolha
e fornecer feedback educativo e motivador.

Se o aluno acertou: parabenize-o e reforce o conceito correto.
Se o aluno errou: explique gentilmente o erro e ensine o conceito correto.
Seja breve, claro e encorajador. Máximo de 3 parágrafos.
"""


async def get_tutor_feedback(
    question: str,
    options: list[str],
    correct_answer: int,
    answer_given: int,
    explanation: str,
    conversation_history: list[dict],
) -> str:
    """Uses the Agno Tutor Agent to generate personalized feedback."""
    agent = Agent(
        model=OpenAIChat(id="gpt-4o-mini", api_key=settings.openai_api_key),
        system_prompt=TUTOR_SYSTEM_PROMPT,
    )

    is_correct = answer_given == correct_answer
    result_label = "CORRETA" if is_correct else "INCORRETA"

    prompt = (
        f"Pergunta: {question}\n"
        f"Alternativas: {', '.join(f'{i}) {opt}' for i, opt in enumerate(options))}\n"
        f"Resposta do aluno: {answer_given}) {options[answer_given]}\n"
        f"Resposta correta: {correct_answer}) {options[correct_answer]}\n"
        f"Resultado: {result_label}\n"
        f"Explicação base: {explanation}\n\n"
        "Forneça seu feedback educativo."
    )

    response = await agent.arun(prompt)
    return response.content
