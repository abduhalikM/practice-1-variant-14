# Практическая работа №1 — вариант 14

Первый этап: модель слоя доступа к данным.

Данные сущностей `Participant`, `Command` и `Reply` хранятся в словарях в
оперативной памяти. Сохранение на диск не производится.

## Запуск демонстрации

```powershell
py -m src.demo
```

## Запуск интерактивного режима REPL

```powershell
py -m src.repl
```

## Запуск тестов

```powershell
py -m unittest discover -s tests
```

В REPL модель доступна через переменную `model`.

Пример:

```python
participant = model.create_participant(
    {
        "ip": "127.0.0.1",
        "locale": "ru-RU",
        "user_agent": "Firefox",
    }
)
model.get_participants()
model.get_participant(participant["id"])
```
