"""Запуск временного TCP-сервера для сетевых тестов."""

import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.client import RpcClient
from src.server import RpcServer


def stop_server(server: RpcServer, thread: threading.Thread) -> None:
    """Остановить сервер и дождаться завершения его потока."""
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def start_server(
    test: unittest.TestCase,
) -> tuple[RpcServer, RpcClient, Path]:
    """Создать изолированный сервер на свободном системном порту."""
    directory = TemporaryDirectory()
    test.addCleanup(directory.cleanup)
    journal = Path(directory.name) / "journal.log"
    server = RpcServer(("127.0.0.1", 0), str(journal))
    thread = threading.Thread(
        target=server.serve_forever,
        kwargs={"poll_interval": 0.01},
        daemon=True,
    )
    test.addCleanup(stop_server, server, thread)
    thread.start()
    host, port = server.server_address
    return server, RpcClient(host, port), journal
