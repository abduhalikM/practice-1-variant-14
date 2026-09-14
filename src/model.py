"""Модель слоя доступа к данным для варианта 14."""

from __future__ import annotations

import time
from typing import Any


Record = dict[str, Any]


class DataModel:
    """Хранит Participant, Command и Reply в оперативной памяти."""

    RECENT_INTERVAL_SECONDS = 8 * 60

    def __init__(self) -> None:
        self.participants: dict[int, Record] = {}
        self.commands: dict[int, Record] = {}
        self.replies: dict[int, Record] = {}

        self._next_ids = {
            "participant": 1,
            "command": 1,
            "reply": 1,
        }

    def _get_next_id(self, entity: str) -> int:
        record_id = self._next_ids[entity]
        self._next_ids[entity] += 1
        return record_id

    @staticmethod
    def _require_fields(data: Record, fields: set[str]) -> None:
        missing = fields - data.keys()

        if missing:
            names = ", ".join(sorted(missing))
            raise ValueError(
                f"Не заполнены обязательные поля: {names}"
            )

    @staticmethod
    def _get_record(
        storage: dict[int, Record],
        record_id: int,
        entity: str,
    ) -> Record:
        try:
            return dict(storage[record_id])
        except KeyError as error:
            raise KeyError(
                f"Запись {entity} с id={record_id} не найдена"
            ) from error

    def create_participant(self, data: Record) -> Record:
        """Создать участника и вернуть созданную запись."""

        required = {
            "ip",
            "locale",
            "user_agent",
        }
        self._require_fields(data, required)

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

        return [
            dict(record)
            for record in self.participants.values()
        ]

    def get_participant(self, record_id: int) -> Record:
        """Получить Participant по идентификатору."""

        return self._get_record(
            self.participants,
            record_id,
            "Participant",
        )

    def create_command(self, data: Record) -> Record:
        """Создать команду и вернуть созданную запись."""

        required = {
            "parameter",
            "participant",
            "description",
            "tags",
            "spawned",
        }
        self._require_fields(data, required)

        participant_id = data["participant"]

        if participant_id not in self.participants:
            raise ValueError(
                "Нельзя создать Command: Participant "
                f"с id={participant_id} не найден"
            )

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

        return [
            dict(record)
            for record in self.commands.values()
        ]

    def get_command(self, record_id: int) -> Record:
        """Получить Command по идентификатору."""

        return self._get_record(
            self.commands,
            record_id,
            "Command",
        )

    def create_reply(self, data: Record) -> Record:
        """Создать ответ и вернуть созданную запись."""

        required = {
            "response",
            "status",
            "exception",
            "command",
            "cache_hit",
            "duration",
        }
        self._require_fields(data, required)

        command_id = data["command"]

        if command_id not in self.commands:
            raise ValueError(
                "Нельзя создать Reply: Command "
                f"с id={command_id} не найден"
            )

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

        return [
            dict(record)
            for record in self.replies.values()
        ]

    def get_reply(self, record_id: int) -> Record:
        """Получить Reply по идентификатору."""

        return self._get_record(
            self.replies,
            record_id,
            "Reply",
        )

    def get_recent_results(
        self,
        now: int | None = None,
    ) -> list[Record]:
        """
        Соединить таблицы и получить результаты
        за последние восемь минут.
        """

        if now is None:
            current_time = int(time.time())
        else:
            current_time = now

        threshold = (
            current_time - self.RECENT_INTERVAL_SECONDS
        )

        result: list[Record] = []

        for command in self.commands.values():
            if command["created"] <= threshold:
                continue

            participant = self.participants[
                command["participant"]
            ]

            command_replies = [
                reply
                for reply in self.replies.values()
                if reply["command"] == command["id"]
            ]

            if not command_replies:
                command_replies = [
                    {"response": None}
                ]

            for reply in command_replies:
                result.append(
                    {
                        "description": command["description"],
                        "ip": participant["ip"],
                        "response": reply["response"],
                    }
                )

        return result