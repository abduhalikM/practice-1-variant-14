"""Проверка связей и внешних соединений первого этапа."""

import unittest

from src.demo import create_records
from src.model import DataModel


class ModelJoinTests(unittest.TestCase):
    """Проверяет время отбора и кратность связанных записей."""

    def test_time_boundary_and_missing_reply(self) -> None:
        """Сохранить команду без ответа и исключить границу времени."""
        model = DataModel()
        participant, command, _ = create_records(model)
        model.replies.clear()
        model.commands[command["id"]]["created"] = 1000
        expected = [{
            "description": command["description"],
            "ip": participant["ip"],
            "response": None,
        }]
        boundary = 1000 + model.recent_interval_seconds
        self.assertEqual(model.get_recent_results(now=boundary - 1), expected)
        self.assertEqual(model.get_recent_results(now=boundary), [])
        self.assertEqual(model.get_recent_results(now=boundary + 1), [])

    def test_many_commands_and_replies(self) -> None:
        """Соединить несколько команд участника и несколько ответов."""
        model = DataModel()
        participant, command, reply = create_records(model)
        data = {key: value for key, value in command.items() if key != "id"}
        second_command = model.create_command(data)
        reply_data = {
            key: value for key, value in reply.items() if key != "id"
        }
        reply_data["response"] = "Второй ответ"
        model.create_reply(reply_data)
        rows = model.get_recent_results(now=command["created"])
        self.assertEqual(len(rows), 3)
        self.assertEqual(
            [row["response"] for row in rows],
            [reply["response"], "Второй ответ", None],
        )
        self.assertTrue(all(row["ip"] == participant["ip"] for row in rows))
        self.assertEqual(second_command["participant"], participant["id"])

    def test_unused_participant(self) -> None:
        """Не включать в выборку участника без команд."""
        model = DataModel()
        model.create_participant({
            "ip": "127.0.0.1", "locale": "ru-RU", "user_agent": "Test",
        })
        self.assertEqual(model.get_recent_results(), [])
