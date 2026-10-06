"""TCP-сервер удалённых вызовов десяти методов модели."""

import json
import socketserver
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config import connection_timeout, parse_address
from src.model import DataModel
from src.protocol import (
    ProtocolError, encode_message, operation_codes, receive_message,
)


def error_response(error: Exception) -> dict[str, Any]:
    """Представить исключение в формате ответа RPC."""
    return {
        "ok": False,
        "error": type(error).__name__,
        "message": str(error),
    }


class RpcServer(socketserver.ThreadingTCPServer):
    """Хранит общую модель в памяти и журналирует ответы клиентов."""

    allow_reuse_address = True
    daemon_threads = True

    def __init__(
        self, address: tuple[str, int], log_path: str = "journal.log"
    ) -> None:
        """Создать модель, журнал и слушающий TCP-сокет."""
        self.model = DataModel()
        self.lock = threading.Lock()
        self.log_path = Path(log_path)
        self.methods = {
            code: getattr(self.model, name)
            for name, code in operation_codes.items()
        }
        super().__init__(address, RpcHandler)

    def dispatch(
        self, operation: int, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Вызвать метод модели или вернуть описание ошибки."""
        with self.lock:
            try:
                if operation not in self.methods:
                    raise ValueError(f"Неизвестный код операции: {operation}")
                result = self.methods[operation](**arguments)
                return {"ok": True, "result": result}
            except Exception as error:
                return error_response(error)

    def write_log(self, operation: int, response: dict[str, Any]) -> None:
        """Добавить полный ответ RPC в journal.log в формате JSON Lines."""
        entry = {
            "time": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "response": response,
        }
        with self.lock:
            with self.log_path.open("a", encoding="utf-8") as journal:
                journal.write(json.dumps(entry, ensure_ascii=False) + "\n")


class RpcHandler(socketserver.BaseRequestHandler):
    """Обрабатывает сообщения одного TCP-соединения."""

    def handle(self) -> None:
        """Получать запросы, вызывать модель и отправлять ответы."""
        self.request.settimeout(connection_timeout)
        try:
            self._handle_messages()
        except (EOFError, OSError):
            return

    def _handle_messages(self) -> None:
        """Обработать последовательность запросов клиента."""
        while True:
            try:
                operation, arguments = receive_message(self.request)
            except ProtocolError as error:
                self._reply(error.operation, error_response(error))
                return
            response = self.server.dispatch(operation, arguments)
            self._reply(operation, response)

    def _reply(self, operation: int, response: dict[str, Any]) -> None:
        """Записать ответ в журнал и передать его клиенту."""
        try:
            payload = encode_message(operation, response)
        except ValueError as error:
            response = error_response(error)
            payload = encode_message(operation, response)
        self.server.write_log(operation, response)
        self.request.sendall(payload)


def main() -> None:
    """Запустить сервер до нажатия Ctrl+C."""
    address = parse_address("RPC-сервер для варианта 14")
    try:
        with RpcServer(address) as server:
            host, port = server.server_address
            print("RPC-сервер: {}:{}".format(host, port))
            print("Ответы записываются в journal.log. Выход: Ctrl+C.")
            server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
    except (OSError, OverflowError) as error:
        print(f"Не удалось запустить сервер: {error}")


if __name__ == "__main__":
    main()
