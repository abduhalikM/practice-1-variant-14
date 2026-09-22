"""Проверка операций модели данных."""

import unittest

from src.model import DataModel


class DataModelTests(unittest.TestCase):
    """Проверяет создание, чтение, связи и выборку."""

    def set_up(self) -> None:
        """Создать пустую модель для теста."""
        self.model = DataModel()
        self.participant = self.model.create_participant(
            {
                "created": 1000,
                "ip": "127.0.0.1",
                "locale": "ru-RU",
                "user_agent": "Test",
            }
        )

    def test_participant_operations(self) -> None:
        """Проверить операции Participant."""
        self.set_up()
        self.assertEqual(self.model.get_participants(), [self.participant])
        found = self.model.get_participant(self.participant["id"])
        self.assertEqual(found, self.participant)

    def test_command_and_reply_operations(self) -> None:
        """Проверить операции Command и Reply."""
        self.set_up()
        command, reply = self._create_command_and_reply()
        self.assertEqual(self.model.get_commands(), [command])
        self.assertEqual(self.model.get_command(command["id"]), command)
        self.assertEqual(self.model.get_replies(), [reply])
        self.assertEqual(self.model.get_reply(reply["id"]), reply)

    def test_recent_results(self) -> None:
        """Проверить соединение и ограничение в восемь минут."""
        self.set_up()
        self._create_command_and_reply(created=1000)
        self._create_command_and_reply(created=500)
        result = self.model.get_recent_results(now=1100)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["ip"], "127.0.0.1")
        self.assertEqual(result[0]["description"], "Команда")
        self.assertEqual(result[0]["response"], "Ответ")

    def test_errors(self) -> None:
        """Проверить ошибки связей и идентификаторов."""
        self.set_up()
        with self.assertRaises(KeyError):
            self.model.get_participant(999)
        with self.assertRaises(ValueError):
            self.model.create_command(
                {
                    "parameter": "p",
                    "participant": 999,
                    "description": "Команда",
                    "tags": "test",
                    "spawned": 0,
                }
            )

    def _create_command_and_reply(
        self, created: int = 1000
    ) -> tuple[dict, dict]:
        """Создать связанные Command и Reply для тестов."""
        command = self.model.create_command(
            {
                "created": created,
                "parameter": "p",
                "participant": self.participant["id"],
                "description": "Команда",
                "tags": "test",
                "spawned": 0,
            }
        )
        reply = self.model.create_reply(
            {
                "response": "Ответ",
                "status": "success",
                "exception": "",
                "command": command["id"],
                "cache_hit": 0,
                "duration": 1,
            }
        )
        return command, reply


if __name__ == "__main__":
    unittest.main()
