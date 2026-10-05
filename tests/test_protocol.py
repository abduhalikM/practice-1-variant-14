"""Проверка формата сообщений и границ сообщений в потоке TCP."""

import json
import socket
import unittest

from src.protocol import (
    ProtocolError, encode_message, header_size, length_size, max_body_size,
    operation_codes, operation_limit, receive_exact, receive_message,
    send_message,
)


class FragmentedSocket:
    """Имитирует получение потока по одному байту за чтение."""

    def __init__(self, payload: bytes) -> None:
        """Сохранить поток и начальное смещение."""
        self.payload = payload
        self.offset = 0

    def recv(self, size: int) -> bytes:
        """Вернуть не более одного байта потока."""
        chunk = self.payload[self.offset:self.offset + min(size, 1)]
        self.offset += len(chunk)
        return chunk


class ProtocolTests(unittest.TestCase):
    """Проверяет заголовок, JSON, фрагментацию и обрыв соединения."""

    def test_header_format(self) -> None:
        """Проверить пять байт длины и один байт операции."""
        body = {"text": "Я" * 300}
        operation = operation_codes["create_participant"]
        frame = encode_message(operation, body)
        self.assertEqual(frame[:length_size], b"\x00\x00\x00\x02\x64")
        self.assertEqual(len(frame[:length_size]), length_size)
        self.assertEqual(
            int.from_bytes(frame[:length_size], "big"),
            len(frame[header_size:]),
        )
        self.assertEqual(frame[length_size], operation)
        self.assertEqual(json.loads(frame[header_size:].decode()), body)

    def test_fragmented_and_combined_messages(self) -> None:
        """Прочитать два сообщения, поступающие по одному байту."""
        operation = operation_codes["get_participants"]
        body = {"text": "Я" * 300}
        frame = encode_message(operation, body)
        connection = FragmentedSocket(frame + frame)
        self.assertEqual(receive_message(connection), (operation, body))
        self.assertEqual(receive_message(connection), (operation, body))
        with self.assertRaises(EOFError):
            receive_message(connection)

    def test_socket_round_trip(self) -> None:
        """Передать сообщение через реальные соединённые сокеты."""
        sender, receiver = socket.socketpair()
        with sender, receiver:
            sender.settimeout(1)
            receiver.settimeout(1)
            operation = operation_codes["get_reply"]
            body = {"record_id": 1}
            send_message(sender, operation, body)
            self.assertEqual(receive_message(receiver), (operation, body))

    def test_truncated_message(self) -> None:
        """Отклонить недополученный заголовок и недополученное тело."""
        frame = encode_message(operation_codes["get_commands"], {})
        for payload in (frame[:length_size], frame[:-1]):
            with self.subTest(payload=payload):
                with self.assertRaises(EOFError):
                    receive_message(FragmentedSocket(payload))
        self.assertEqual(receive_exact(FragmentedSocket(b""), 0), b"")

    def test_invalid_json(self) -> None:
        """Отклонить неверный JSON, неверный UTF-8 и JSON-массив."""
        operation = operation_codes["get_commands"]
        for payload in (b"{", b"\xff", b"[]"):
            with self.subTest(payload=payload):
                frame = len(payload).to_bytes(length_size, "big")
                frame += bytes([operation]) + payload
                with self.assertRaises(ProtocolError) as caught:
                    receive_message(FragmentedSocket(frame))
                self.assertEqual(caught.exception.operation, operation)

    def test_size_and_operation_limits(self) -> None:
        """Проверить ограничение тела и диапазон байта операции."""
        for operation in (-1, operation_limit, True, "1", None):
            with self.subTest(operation=operation):
                with self.assertRaises(ValueError):
                    encode_message(operation, {})
        with self.assertRaises(ValueError):
            encode_message(operation_codes["get_reply"], [])
        with self.assertRaises(ValueError):
            encode_message(1, {"text": "x" * max_body_size})
        header = (max_body_size + 1).to_bytes(length_size, "big")
        with self.assertRaises(ProtocolError):
            receive_message(FragmentedSocket(header + bytes([1])))
