"""Демонстрация всех десяти удалённых методов и обработки ошибок."""

from src.client import RpcClient, RpcError
from src.config import parse_address
from src.demo import create_records, show_operations


def show_errors(client: RpcClient) -> None:
    """Показать ошибки отсутствующей записи и неправильной связи."""
    try:
        client.get_participant(-1)
    except RpcError as error:
        print("Ожидаемая ошибка:", error)
    try:
        client.create_command(
            {
                "parameter": "test",
                "participant": -1,
                "description": "Неверная связь",
                "tags": "demo",
                "spawned": 0,
            }
        )
    except RpcError as error:
        print("Ожидаемая ошибка:", error)


def main() -> None:
    """Вызвать все методы модели через клиент TCP."""
    host, port = parse_address("Демонстрация всех методов RPC")
    client = RpcClient(host, port)
    try:
        records = create_records(client)
        print("Созданы Participant, Command и Reply:", records)
        show_operations(client, records)
        show_errors(client)
    except OSError as error:
        print(f"Не удалось подключиться к серверу: {error}")


if __name__ == "__main__":
    main()
