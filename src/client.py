"""Клиент RPC с теми же десятью методами, что и модель данных."""

from __future__ import annotations

import code
import socket
from typing import Any

from src.config import (
    connection_timeout, default_host, default_port, parse_address,
)
from src.model import Record
from src.protocol import operation_codes, receive_message, send_message


class RpcError(RuntimeError):
    """Ошибка, полученная от удалённой модели."""

    def __init__(self, error_type: str, message: str) -> None:
        """Сохранить тип и описание ошибки сервера."""
        self.error_type = error_type
        super().__init__(f"{error_type}: {message}")


class RpcClient:
    """Передаёт вызовы модели на сервер через TCP."""

    def __init__(
        self, host: str = default_host, port: int = default_port
    ) -> None:
        """Сохранить адрес сервера без открытия соединения."""
        self.address = host, port

    def _call(self, method: str, arguments: Record) -> Any:
        """Отправить запрос и вернуть результат или ошибку сервера."""
        operation = operation_codes[method]
        with socket.create_connection(
            self.address, timeout=connection_timeout
        ) as connection:
            send_message(connection, operation, arguments)
            response_code, response = receive_message(connection)
        if response_code != operation:
            raise ValueError("Код ответа не совпадает с кодом запроса")
        if response.get("ok") is False:
            raise RpcError(response["error"], response["message"])
        if response.get("ok") is not True or "result" not in response:
            raise ValueError("Некорректная структура ответа RPC")
        return response["result"]

    def create_participant(self, data: Record) -> Record:
        """Удалённо создать Participant."""
        return self._call("create_participant", {"data": data})

    def get_participants(self) -> list[Record]:
        """Удалённо получить все Participant."""
        return self._call("get_participants", {})

    def get_participant(self, record_id: int) -> Record:
        """Удалённо получить Participant по идентификатору."""
        return self._call("get_participant", {"record_id": record_id})

    def create_command(self, data: Record) -> Record:
        """Удалённо создать Command."""
        return self._call("create_command", {"data": data})

    def get_commands(self) -> list[Record]:
        """Удалённо получить все Command."""
        return self._call("get_commands", {})

    def get_command(self, record_id: int) -> Record:
        """Удалённо получить Command по идентификатору."""
        return self._call("get_command", {"record_id": record_id})

    def create_reply(self, data: Record) -> Record:
        """Удалённо создать Reply."""
        return self._call("create_reply", {"data": data})

    def get_replies(self) -> list[Record]:
        """Удалённо получить все Reply."""
        return self._call("get_replies", {})

    def get_reply(self, record_id: int) -> Record:
        """Удалённо получить Reply по идентификатору."""
        return self._call("get_reply", {"record_id": record_id})

    def get_recent_results(self, now: int | None = None) -> list[Record]:
        """Удалённо получить соединённую выборку за восемь минут."""
        return self._call("get_recent_results", {"now": now})


def main() -> None:
    """Открыть REPL для удалённой модели в переменной client."""
    host, port = parse_address("Интерактивный клиент RPC")
    client = RpcClient(host, port)
    message = (
        "RPC-клиент: {}:{}. Сначала запустите сервер.\n"
        "Пример: client.get_participants()\n"
        "Для выхода выполните exit()."
    ).format(host, port)
    code.interact(banner=message, local={"client": client})


if __name__ == "__main__":
    main()
