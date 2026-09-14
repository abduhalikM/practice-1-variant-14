"""Демонстрация всей функциональности первого этапа."""

import time

from .model import DataModel


def print_section(title: str) -> None:
    """Напечатать заголовок части демонстрации."""

    print(f"\n--- {title} ---")


def main() -> None:
    """Продемонстрировать функции модели и ошибки."""

    model = DataModel()

    print_section("Создание Participant")

    participant = model.create_participant(
        {
            "ip": "127.0.0.1",
            "locale": "ru-RU",
            "user_agent": "PyCharm demo",
        }
    )

    print(participant)

    print_section("Получение всех Participant")
    print(model.get_participants())

    print_section("Получение Participant по id")
    print(model.get_participant(participant["id"]))

    print_section("Создание Command")

    command = model.create_command(
        {
            "parameter": "name=student",
            "participant": participant["id"],
            "description": "Демонстрационная команда",
            "tags": "demo,variant-14",
            "spawned": 0,
        }
    )

    print(command)

    print_section("Получение всех Command")
    print(model.get_commands())

    print_section("Получение Command по id")
    print(model.get_command(command["id"]))

    print_section("Создание Reply")

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

    print(reply)

    print_section("Получение всех Reply")
    print(model.get_replies())

    print_section("Получение Reply по id")
    print(model.get_reply(reply["id"]))

    print_section(
        "Соединённая выборка за последние 8 минут"
    )

    print(
        model.get_recent_results(
            now=int(time.time())
        )
    )

    print_section(
        "Обработка несуществующего идентификатора"
    )

    try:
        model.get_participant(999)
    except KeyError as error:
        print(f"Ожидаемая ошибка: {error}")

    print_section(
        "Обработка неправильной связи"
    )

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
        print(f"Ожидаемая ошибка: {error}")


if __name__ == "__main__":
    main()