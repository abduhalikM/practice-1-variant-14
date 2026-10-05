"""Адрес и параметры TCP-соединения."""

import argparse


default_host = "127.0.0.1"
default_port = 9000
connection_timeout = 5.0


def parse_address(description: str) -> tuple[str, int]:
    """Прочитать адрес сервера из аргументов командной строки."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--host", default=default_host)
    parser.add_argument("--port", type=int, default=default_port)
    arguments = parser.parse_args()
    return arguments.host, arguments.port
