"""Демонстрация функциональности первого этапа."""

from src.model import DataModel, Record


def create_records(model: DataModel) -> tuple[Record, Record, Record]:
    """Создать связанные записи трёх сущностей."""
    participant = model.create_participant(
        {
            "ip": "127.0.0.1",
            "locale": "ru-RU",
            "user_agent": "Demo",
        }
    )
    command = model.create_command(
        {
            "parameter": "name=student",
            "participant": participant["id"],
            "description": "Демонстрационная команда",
            "tags": "demo,variant-14",
            "spawned": 0,
        }
    )
    reply = model.create_reply(
        {
            "response": "Команда выполнена",
            "status": "success",
            "exception": "",
            "command": command["id"],
            "cache_hit": 0,
            "duration": 15,
        }
    )
    return participant, command, reply


def show_operations(
    model: DataModel, records: tuple[Record, Record, Record]
) -> None:
    """Показать операции чтения и соединённую выборку."""
    participant, command, reply = records
    print("Все Participant:", model.get_participants())
    print("Participant по id:", model.get_participant(participant["id"]))
    print("Все Command:", model.get_commands())
    print("Command по id:", model.get_command(command["id"]))
    print("Все Reply:", model.get_replies())
    print("Reply по id:", model.get_reply(reply["id"]))
    print("Выборка за 8 минут:", model.get_recent_results())


def show_errors(model: DataModel) -> None:
    """Показать обработку ошибочных операций."""
    try:
        model.get_participant(999)
    except KeyError as error:
        print("Ожидаемая ошибка:", error)
    try:
        model.create_reply(
            {
                "response": "Ошибка",
                "status": "failed",
                "exception": "Command не существует",
                "command": 999,
                "cache_hit": 0,
                "duration": 0,
            }
        )
    except ValueError as error:
        print("Ожидаемая ошибка:", error)


def main() -> None:
    """Запустить демонстрацию модели."""
    model = DataModel()
    records = create_records(model)
    show_operations(model, records)
    show_errors(model)


if __name__ == "__main__":
    main()
