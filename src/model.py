"""Модель слоя доступа к данным для варианта 14."""

from __future__ import annotations

import time
from typing import Any


Record = dict[str, Any]


class DataModel:
    """Хранит записи Participant, Command и Reply в памяти."""

    recent_interval_seconds = 8 * 60

    def __init__(self) -> None:
        """Создать пустые таблицы и счётчики идентификаторов."""
        self.participants: dict[int, Record] = {}
        self.commands: dict[int, Record] = {}
        self.replies: dict[int, Record] = {}
        self._next_ids = {"participant": 1, "command": 1, "reply": 1}

    def _get_next_id(self, entity: str) -> int:
        """Вернуть следующий идентификатор сущности."""
        record_id = self._next_ids[entity]
        self._next_ids[entity] += 1
        return record_id

    @staticmethod
    def _require_fields(data: Record, fields: set[str]) -> None:
        """Проверить наличие обязательных полей."""
        missing = fields - data.keys()
        if missing:
            names = ", ".join(sorted(missing))
            raise ValueError(f"Не заполнены обязательные поля: {names}")

    @staticmethod
    def _get_record(
        storage: dict[int, Record], record_id: int, entity: str
    ) -> Record:
        """Получить копию записи или сообщить об ошибке."""
        if record_id not in storage:
            raise KeyError(f"Запись {entity} с id={record_id} не найдена")
        return dict(storage[record_id])

    def create_participant(self, data: Record) -> Record:
        """Создать запись Participant."""
        self._require_fields(data, {"ip", "locale", "user_agent"})
        record_id = self._get_next_id("participant")
        record = {
            "id": record_id,
            "created": data.get("created", int(time.time())),
            "ip": data["ip"],
            "locale": data["locale"],
            "user_agent": data["user_agent"],
        }
        self.participants[record_id] = record
        return dict(record)

    def get_participants(self) -> list[Record]:
        """Получить все записи Participant."""
        return [dict(item) for item in self.participants.values()]

    def get_participant(self, record_id: int) -> Record:
        """Получить Participant по идентификатору."""
        return self._get_record(self.participants, record_id, "Participant")

    def create_command(self, data: Record) -> Record:
        """Создать запись Command."""
        required = {
            "parameter", "participant", "description", "tags", "spawned"
        }
        self._require_fields(data, required)
        participant_id = data["participant"]
        if participant_id not in self.participants:
            raise ValueError(f"Participant с id={participant_id} не найден")
        record_id = self._get_next_id("command")
        record = {
            "id": record_id,
            "created": data.get("created", int(time.time())),
            "parameter": data["parameter"],
            "participant": participant_id,
            "description": data["description"],
            "tags": data["tags"],
            "spawned": data["spawned"],
        }
        self.commands[record_id] = record
        return dict(record)

    def get_commands(self) -> list[Record]:
        """Получить все записи Command."""
        return [dict(item) for item in self.commands.values()]

    def get_command(self, record_id: int) -> Record:
        """Получить Command по идентификатору."""
        return self._get_record(self.commands, record_id, "Command")

    def create_reply(self, data: Record) -> Record:
        """Создать запись Reply."""
        required = {
            "response", "status", "exception", "command",
            "cache_hit", "duration",
        }
        self._require_fields(data, required)
        command_id = data["command"]
        if command_id not in self.commands:
            raise ValueError(f"Command с id={command_id} не найден")
        record_id = self._get_next_id("reply")
        record = {
            "id": record_id,
            "created": data.get("created", int(time.time())),
            "response": data["response"],
            "status": data["status"],
            "exception": data["exception"],
            "command": command_id,
            "cache_hit": data["cache_hit"],
            "duration": data["duration"],
        }
        self.replies[record_id] = record
        return dict(record)

    def get_replies(self) -> list[Record]:
        """Получить все записи Reply."""
        return [dict(item) for item in self.replies.values()]

    def get_reply(self, record_id: int) -> Record:
        """Получить Reply по идентификатору."""
        return self._get_record(self.replies, record_id, "Reply")

    def _rows_for_command(self, command: Record) -> list[Record]:
        """Соединить одну Command с Participant и Reply."""
        participant = self.participants[command["participant"]]
        replies = [
            item
            for item in self.replies.values()
            if item["command"] == command["id"]
        ]
        if not replies:
            replies = [{"response": None}]
        return [
            {
                "description": command["description"],
                "ip": participant["ip"],
                "response": reply["response"],
            }
            for reply in replies
        ]

    def get_recent_results(
        self, now: int | None = None
    ) -> list[Record]:
        """Получить соединённые данные за последние восемь минут."""
        current_time = int(time.time()) if now is None else now
        threshold = current_time - self.recent_interval_seconds
        result: list[Record] = []
        for command in self.commands.values():
            if command["created"] > threshold:
                result.extend(self._rows_for_command(command))
        return result
