import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

from fastapi import HTTPException

from app.models.flashcard import Flashcard
from app.models.quiz import Quiz
from app.models.session import SessionAnswer, StudySession
from app.models.user import User
from app.routers.quiz import get_quiz, list_quizzes
from app.routers.sessions import (
    finish_session,
    get_session,
    list_sessions,
    start_session,
    submit_answer,
)
from app.schemas.session import AnswerRequest, StartSessionRequest


def build_query_mock(*, all_result=None, first_result=None, count_result=None):
    query = MagicMock()
    query.filter.return_value = query
    query.order_by.return_value = query
    query.all.return_value = all_result if all_result is not None else []
    query.first.return_value = first_result
    query.count.return_value = count_result if count_result is not None else 0
    return query


class RouteBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.user = User(
            id=uuid.uuid4(),
            email="user@example.com",
            password_hash="hashed",
            name="User",
        )
        self.other_user = User(
            id=uuid.uuid4(),
            email="other@example.com",
            password_hash="hashed",
            name="Other",
        )
        self.quiz = Quiz(
            id=uuid.uuid4(),
            video_id=uuid.uuid4(),
            user_id=self.user.id,
            summary="Resumo",
        )
        self.flashcard_one = Flashcard(
            id=uuid.uuid4(),
            quiz_id=self.quiz.id,
            question="Pergunta 1",
            options=["A", "B", "C", "D"],
            correct_answer=1,
            explanations=["Exp A", "Exp B", "Exp C", "Exp D"],
            position=1,
        )
        self.flashcard_two = Flashcard(
            id=uuid.uuid4(),
            quiz_id=self.quiz.id,
            question="Pergunta 2",
            options=["A", "B", "C", "D"],
            correct_answer=3,
            explanations=["Exp A2", "Exp B2", "Exp C2", "Exp D2"],
            position=2,
        )
        self.session = StudySession(
            id=uuid.uuid4(),
            user_id=self.user.id,
            quiz_id=self.quiz.id,
            score=None,
            total=None,
            started_at=datetime.now(timezone.utc),
            finished_at=None,
        )

    def test_get_quiz_returns_owned_quiz_with_flashcards(self):
        db = MagicMock()
        db.get.return_value = self.quiz
        db.query.return_value = build_query_mock(
            all_result=[self.flashcard_one, self.flashcard_two]
        )

        response = get_quiz(self.quiz.id, db=db, current_user=self.user)

        self.assertEqual(response.id, self.quiz.id)
        self.assertEqual(len(response.flashcards), 2)
        self.assertEqual(response.flashcards[0].explanations[1], "Exp B")

    def test_list_quizzes_returns_only_current_user_items(self):
        db = MagicMock()
        quiz_query = build_query_mock(all_result=[self.quiz])
        flashcard_query = build_query_mock(all_result=[self.flashcard_one])
        db.query.side_effect = [quiz_query, flashcard_query]

        response = list_quizzes(db=db, current_user=self.user)

        self.assertEqual(len(response), 1)
        self.assertEqual(response[0].user_id, self.user.id)
        self.assertEqual(response[0].flashcards[0].question, "Pergunta 1")

    def test_start_session_creates_session_for_owned_quiz(self):
        db = MagicMock()
        db.get.return_value = self.quiz

        def refresh_session(session):
            session.id = self.session.id
            session.started_at = self.session.started_at
            session.finished_at = None

        db.refresh.side_effect = refresh_session

        response = start_session(
            StartSessionRequest(quiz_id=self.quiz.id),
            db=db,
            current_user=self.user,
        )

        self.assertEqual(response.quiz_id, self.quiz.id)
        self.assertIsNone(response.finished_at)
        db.add.assert_called_once()

    def test_submit_answer_returns_selected_and_correct_explanations(self):
        db = MagicMock()
        duplicate_query = build_query_mock(first_result=None)
        db.get.side_effect = [self.session, self.flashcard_one]
        db.query.return_value = duplicate_query

        response = submit_answer(
            self.session.id,
            AnswerRequest(flashcard_id=self.flashcard_one.id, answer_given=0),
            db=db,
            current_user=self.user,
        )

        self.assertFalse(response.is_correct)
        self.assertEqual(response.correct_answer, 1)
        self.assertEqual(response.selected_explanation, "Exp A")
        self.assertEqual(response.correct_explanation, "Exp B")

    def test_submit_answer_rejects_duplicate_flashcard(self):
        db = MagicMock()
        duplicate_query = build_query_mock(first_result=SessionAnswer())
        db.get.side_effect = [self.session, self.flashcard_one]
        db.query.return_value = duplicate_query

        with self.assertRaises(HTTPException) as ctx:
            submit_answer(
                self.session.id,
                AnswerRequest(flashcard_id=self.flashcard_one.id, answer_given=1),
                db=db,
                current_user=self.user,
            )

        self.assertEqual(ctx.exception.status_code, 409)

    def test_finish_session_calculates_score_and_total(self):
        db = MagicMock()
        answers_query = build_query_mock(count_result=1)
        flashcards_query = build_query_mock(count_result=2)
        db.get.return_value = self.session
        db.query.side_effect = [answers_query, flashcards_query]

        response = finish_session(self.session.id, db=db, current_user=self.user)

        self.assertEqual(response.score, 1)
        self.assertEqual(response.total, 2)
        self.assertIsNotNone(response.finished_at)

    def test_get_session_returns_owned_session(self):
        db = MagicMock()
        db.get.return_value = self.session

        response = get_session(self.session.id, db=db, current_user=self.user)

        self.assertEqual(response.id, self.session.id)
        self.assertEqual(response.quiz_id, self.quiz.id)

    def test_list_sessions_returns_history_for_current_user(self):
        db = MagicMock()
        db.query.return_value = build_query_mock(all_result=[self.session])

        response = list_sessions(db=db, current_user=self.user)

        self.assertEqual(len(response), 1)
        self.assertEqual(response[0].id, self.session.id)

    def test_get_quiz_rejects_other_users_quiz(self):
        db = MagicMock()
        db.get.return_value = Quiz(
            id=uuid.uuid4(),
            video_id=uuid.uuid4(),
            user_id=self.other_user.id,
            summary="Outro",
        )

        with self.assertRaises(HTTPException) as ctx:
            get_quiz(uuid.uuid4(), db=db, current_user=self.user)

        self.assertEqual(ctx.exception.status_code, 404)
