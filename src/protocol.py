"""Сообщения RPC: 5 байт длины, 1 байт операции и JSON в UTF-8."""

import json
import socket
from typing import Any


length_size = 5
header_size = length_size + 1
operation_limit = 1 << 8
operation_min = 0
max_body_size = 1024 * 1024
method_names = (
    "create_participant", "get_participants", "get_participant",
    "create_command", "get_commands", "get_command",
    "create_reply", "get_replies", "get_reply", "get_recent_results",
)
operation_codes = {
    name: code for code, name in enumerate(method_names, start=1)
}


class ProtocolError(ValueError):
    """Ошибка сообщения с сохранением кода операции."""

    def __init__(self, message: str, operation: int) -> None:
        """Сохранить описание ошибки и код полученной операции."""
        super().__init__(message)
        self.operation = operation


def receive_exact(connection: socket.socket, size: int) -> bytes:
    """Прочитать указанное число байтов, учитывая фрагментацию TCP."""
    chunks = bytearray()
    while len(chunks) < size:
        chunk = connection.recv(size - len(chunks))
        if not chunk:
            raise EOFError("Соединение закрыто до получения сообщения")
        chunks.extend(chunk)
    return bytes(chunks)


def encode_message(operation: int, body: dict[str, Any]) -> bytes:
    """Сформировать заголовок и тело сообщения RPC."""
    valid_code = (
        type(operation) is int
        and operation_min <= operation < operation_limit
    )
    if not valid_code:
        raise ValueError("Код операции должен помещаться в один байт")
    if not isinstance(body, dict):
        raise ValueError("Тело сообщения должно быть JSON-объектом")
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    if len(payload) > max_body_size:
        raise ValueError("Размер тела превышает 1 МиБ")
    header = len(payload).to_bytes(length_size, "big") + bytes([operation])
    return header + payload


def send_message(
    connection: socket.socket, operation: int, body: dict[str, Any]
) -> None:
    """Отправить длину тела в big-endian, код операции и JSON."""
    connection.sendall(encode_message(operation, body))


def receive_message(
    connection: socket.socket,
) -> tuple[int, dict[str, Any]]:
    """Получить и проверить одно сообщение из потока TCP."""
    header = receive_exact(connection, header_size)
    body_size = int.from_bytes(header[:length_size], "big")
    operation = header[length_size]
    if body_size > max_body_size:
        raise ProtocolError("Размер тела превышает 1 МиБ", operation)
    payload = receive_exact(connection, body_size)
    try:
        body = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProtocolError("Некорректный JSON в UTF-8", operation) from error
    if not isinstance(body, dict):
        raise ProtocolError("Тело должно быть JSON-объектом", operation)
    return operation, body
