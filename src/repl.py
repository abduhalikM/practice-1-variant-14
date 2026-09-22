"""Интерактивный режим работы с моделью данных."""

import code

from src.model import DataModel


def main() -> None:
    """Создать модель и открыть интерактивную консоль."""
    model = DataModel()
    message = (
        "Модель создана в переменной model.\n"
        "Пример команды: model.get_participants()\n"
        "Для выхода выполните exit()."
    )
    code.interact(banner=message, local={"model": model})


if __name__ == "__main__":
    main()
