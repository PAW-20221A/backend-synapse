import unittest

from app.services.quiz_agent import validate_quiz_payload


class QuizAgentValidationTests(unittest.TestCase):
    def test_validate_quiz_payload_accepts_aligned_explanations(self):
        payload = {
            "summary": "Resumo",
            "flashcards": [
                {
                    "question": "Pergunta 1",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": 2,
                    "explanations": [
                        "A incorreta",
                        "B incorreta",
                        "C correta",
                        "D incorreta",
                    ],
                }
            ],
        }

        validated = validate_quiz_payload(payload, question_count=1)

        self.assertEqual(validated["summary"], "Resumo")
        self.assertEqual(validated["flashcards"][0]["explanations"][2], "C correta")

    def test_validate_quiz_payload_rejects_misaligned_explanations(self):
        payload = {
            "summary": "Resumo",
            "flashcards": [
                {
                    "question": "Pergunta 1",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": 1,
                    "explanations": ["A incorreta", "B correta"],
                }
            ],
        }

        with self.assertRaisesRegex(ValueError, "Invalid quiz payload"):
            validate_quiz_payload(payload, question_count=1)

    def test_validate_quiz_payload_rejects_out_of_range_correct_answer(self):
        payload = {
            "summary": "Resumo",
            "flashcards": [
                {
                    "question": "Pergunta 1",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": 4,
                    "explanations": [
                        "A incorreta",
                        "B incorreta",
                        "C incorreta",
                        "D incorreta",
                    ],
                }
            ],
        }

        with self.assertRaisesRegex(ValueError, "Invalid quiz payload"):
            validate_quiz_payload(payload, question_count=1)

    def test_validate_quiz_payload_rejects_wrong_flashcard_count(self):
        payload = {
            "summary": "Resumo",
            "flashcards": [
                {
                    "question": "Pergunta 1",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": 0,
                    "explanations": [
                        "A correta",
                        "B incorreta",
                        "C incorreta",
                        "D incorreta",
                    ],
                }
            ],
        }

        with self.assertRaisesRegex(ValueError, "unexpected number of flashcards"):
            validate_quiz_payload(payload, question_count=2)
