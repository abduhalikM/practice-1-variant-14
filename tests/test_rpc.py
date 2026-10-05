"""Интеграционные проверки RPC через настоящий TCP-сервер."""

import inspect
import json
import socket
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from src.client import RpcClient, RpcError
from src.demo import create_records
from src.model import DataModel
from src.protocol import (
    encode_message, length_size, max_body_size, method_names, operation_codes,
    receive_message, send_message,
)
from tests.helpers import start_server


class RpcTests(unittest.TestCase):
    """Проверяет десять методов, ошибки, общий сервер и journal.log."""

    def set_up(self) -> None:
        """Создать отдельный TCP-сервер и клиент для теста."""
        self.server, self.client, self.journal = start_server(self)

    def test_client_interface(self) -> None:
        """Сравнить имена и параметры методов клиента и модели."""
        for name in method_names:
            with self.subTest(method=name):
                model_method = getattr(DataModel, name)
                client_method = getattr(RpcClient, name)
                self.assertEqual(
                    inspect.signature(client_method),
                    inspect.signature(model_method),
                )

    def test_all_methods(self) -> None:
        """Вызвать все десять методов модели через TCP."""
        self.set_up()
        participant, command, reply = create_records(self.client)
        self.assertEqual(self.client.get_participants(), [participant])
        self.assertEqual(
            self.client.get_participant(participant["id"]), participant
        )
        self.assertEqual(self.client.get_commands(), [command])
        self.assertEqual(self.client.get_command(command["id"]), command)
        self.assertEqual(self.client.get_replies(), [reply])
        self.assertEqual(self.client.get_reply(reply["id"]), reply)
        self.assertEqual(
            self.client.get_recent_results(),
            [{
                "description": command["description"],
                "ip": participant["ip"],
                "response": reply["response"],
            }],
        )
        boundary = command["created"] + DataModel.recent_interval_seconds
        self.assertEqual(self.client.get_recent_results(now=boundary), [])
        entries = self._read_journal()
        self.assertEqual(
            {entry["operation"] for entry in entries},
            set(operation_codes.values()),
        )
        self.assertEqual(entries[-1]["response"], {"ok": True, "result": []})

    def test_errors_are_logged(self) -> None:
        """Проверить передачу и журналирование ошибок модели."""
        self.set_up()
        with self.assertRaises(RpcError) as caught:
            self.client.get_participant(-1)
        self.assertEqual(caught.exception.error_type, "KeyError")
        with self.assertRaises(RpcError):
            self.client.create_participant({})
        with self.assertRaises(RpcError):
            self.client.create_command({
                "participant": -1, "parameter": "p", "description": "d",
                "tags": "t", "spawned": 0,
            })
        with self.assertRaises(RpcError):
            self.client.create_reply({
                "command": -1, "response": "r", "status": "failed",
                "exception": "", "cache_hit": 0, "duration": 0,
            })
        self.assertTrue(all(
            entry["response"]["ok"] is False
            for entry in self._read_journal()
        ))
        self.assertEqual(self.client.get_participants(), [])

    def test_invalid_request_and_next_request(self) -> None:
        """Проверить неизвестную операцию и неправильные аргументы."""
        self.set_up()
        with socket.create_connection(self.client.address, timeout=1) as s:
            send_message(s, 255, {})
            operation, response = receive_message(s)
            self.assertEqual(operation, 255)
            self.assertFalse(response["ok"])
            code = operation_codes["get_participant"]
            send_message(s, code, {})
            self.assertEqual(receive_message(s)[1]["error"], "TypeError")
            code = operation_codes["get_participants"]
            send_message(s, code, {})
            self.assertEqual(receive_message(s)[1]["result"], [])

    def test_bad_json_is_logged(self) -> None:
        """Получить ответ об ошибке JSON с исходным кодом операции."""
        self.set_up()
        operation = operation_codes["create_participant"]
        frame = len(b"{").to_bytes(length_size, "big")
        frame += bytes([operation]) + b"{"
        with socket.create_connection(self.client.address, timeout=1) as s:
            s.sendall(frame)
            code, response = receive_message(s)
            self.assertEqual(code, operation)
            self.assertEqual(response["error"], "ProtocolError")
        self.assertEqual(self._read_journal()[0]["response"], response)
        self.assertEqual(self.client.get_participants(), [])

    def test_parallel_clients_share_model(self) -> None:
        """Создать записи параллельно без повторения идентификаторов."""
        self.set_up()
        data = {"ip": "127.0.0.1", "locale": "ru-RU", "user_agent": "Test"}
        client = RpcClient(*self.client.address)
        with ThreadPoolExecutor(max_workers=4) as executor:
            records = list(executor.map(
                client.create_participant, [data] * 8
            ))
        self.assertEqual(len({item["id"] for item in records}), len(records))
        self.assertEqual(len(client.get_participants()), len(records))

    def test_restart_clears_data(self) -> None:
        """Проверить отсутствие сохранённых на диск записей."""
        self.set_up()
        create_records(self.client)
        _, new_client, _ = start_server(self)
        self.assertEqual(new_client.get_participants(), [])
        self.assertEqual(new_client.get_commands(), [])
        self.assertEqual(new_client.get_replies(), [])

    def test_recent_results_without_reply(self) -> None:
        """Получить через TCP команду без ответа как response=None."""
        self.set_up()
        participant = self.client.create_participant({
            "ip": "10.0.0.1", "locale": "ru-RU", "user_agent": "Test",
        })
        command = self.client.create_command({
            "created": 1000, "participant": participant["id"],
            "parameter": "x", "description": "Без ответа",
            "tags": "test", "spawned": 0,
        })
        self.assertEqual(self.client.get_recent_results(now=1100), [{
            "description": command["description"],
            "ip": participant["ip"],
            "response": None,
        }])

    def test_oversized_response(self) -> None:
        """Вернуть журналируемую ошибку вместо слишком большого тела."""
        self.set_up()
        data = {
            "ip": "127.0.0.1", "locale": "ru-RU",
            "user_agent": "x" * (max_body_size // 2),
        }
        participant = self.client.create_participant(data)
        self.client.create_participant(data)
        with self.assertRaises(RpcError) as caught:
            self.client.get_participants()
        self.assertEqual(caught.exception.error_type, "ValueError")
        self.assertFalse(self._read_journal()[-1]["response"]["ok"])
        self.assertEqual(
            self.client.get_participant(participant["id"]), participant
        )

    def test_truncated_request(self) -> None:
        """После оборванного запроса обслужить нового клиента."""
        self.set_up()
        frame = encode_message(operation_codes["get_participants"], {})
        with socket.create_connection(self.client.address, timeout=1) as s:
            s.sendall(frame[:-1])
            s.shutdown(socket.SHUT_WR)
            self.assertEqual(s.recv(1), b"")
        self.assertEqual(self.client.get_participants(), [])

    def test_client_rejects_invalid_response(self) -> None:
        """Отклонить чужой код операции и неверную структуру ответа."""
        self.set_up()
        code = operation_codes["get_participants"]
        responses = [(code + 1, {"ok": True}), (code, {})]
        for response in responses:
            with self.subTest(response=response):
                with patch(
                    "src.client.receive_message", return_value=response
                ):
                    with self.assertRaises(ValueError):
                        self.client.get_participants()

    def test_external_wire_format(self) -> None:
        """Передать несколько готовых кадров в одном TCP-соединении."""
        self.set_up()
        operation = operation_codes["get_participants"]
        frame = encode_message(operation, {})
        with socket.create_connection(self.client.address, timeout=1) as s:
            s.sendall(frame + frame)
            self.assertEqual(receive_message(s), (
                operation, {"ok": True, "result": []}
            ))
            self.assertEqual(receive_message(s), (
                operation, {"ok": True, "result": []}
            ))
        self.assertEqual(len(self._read_journal()), 2)

    def _read_journal(self) -> list[dict]:
        """Прочитать записи временного журнала RPC."""
        return [
            json.loads(line)
            for line in self.journal.read_text(encoding="utf-8").splitlines()
        ]
