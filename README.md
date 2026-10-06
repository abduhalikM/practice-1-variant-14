# Практическая работа №1 - вариант 14

ИКБО-71-24. Выполнены этапы 1 и 2: модель в памяти и RPC по TCP.
Данные Participant, Command и Reply хранятся в словарях и исчезают
после остановки модели или сервера. Ответы RPC записываются в `journal.log`.

Нужен Python 3.10+. Внешние библиотеки для запуска не требуются.
Все команды выполняются в терминале из папки проекта.

## Этап 1: модель данных

Автоматическая демонстрация создания, чтения, выборки и ошибок:

```powershell
py -m src.demo
```

Интерактивная демонстрация:

```powershell
py -m src.repl
```

После появления `>>>` вводить команды Python:

```python
data = {"ip": "127.0.0.1", "locale": "ru-RU", "user_agent": "Firefox"}
p = model.create_participant(data)
model.get_participants()
model.get_participant(p["id"])
data = {"parameter": "x=1", "participant": p["id"]}
data.update({"description": "Проверка", "tags": "demo", "spawned": 0})
c = model.create_command(data)
model.get_commands()
model.get_command(c["id"])
model.get_recent_results()
data = {"response": "Готово", "status": "success", "exception": ""}
data.update({"command": c["id"], "cache_hit": 0, "duration": 15})
r = model.create_reply(data)
model.get_replies()
model.get_reply(r["id"])
model.get_recent_results()
model.get_participant(-1)
exit()
```

Первая выборка содержит `response = None`, вторая - текст ответа.
Запрос с `-1` показывает ожидаемый `KeyError` и не завершает REPL.

## Этап 2: удалённые вызовы

В первом терминале запустить сервер и оставить его работающим:

```powershell
py -m src.server
```

Во втором терминале запустить демонстрацию всех 10 удалённых методов:

```powershell
py -m src.rpc_demo
```

Для интерактивной работы во втором терминале:

```powershell
py -m src.client
```

После появления `>>>`:

```python
client.get_participants()
client.get_recent_results()
client.get_participant(-1)
exit()
```

Ожидаемая ошибка - `RpcError`. Для создания и чтения записей можно повторить
команды первого этапа, заменив `model` на `client`.
Остановка сервера - `Ctrl+C`. После перезапуска данные пустые.

Посмотреть журнал в PowerShell:

```powershell
Get-Content journal.log -Encoding utf8
```

## Методы и настройки

У модели и клиента одинаковые методы и параметры. Создание принимает словарь
`data`, чтение одной записи - `record_id`, выборка - необязательное время `now`.

| Коды RPC | Методы | Назначение |
|---|---|---|
| 1, 2, 3 | `create_participant`, `get_participants`, `get_participant` | Создать, все, по id |
| 4, 5, 6 | `create_command`, `get_commands`, `get_command` | Создать, все, по id |
| 7, 8, 9 | `create_reply`, `get_replies`, `get_reply` | Создать, все, по id |
| 10 | `get_recent_results` | Соединённая выборка |

Связи: `Participant.id = Command.participant`, `Command.id = Reply.command`.
Выборка отбирает `Command.created > now - 480`, сохраняет команды без ответа
и возвращает уникальные строки с `description`, `ip`, `response`.
`id` назначается автоматически; `created` по умолчанию - текущее Unix-время.

Адрес по умолчанию - `127.0.0.1:9000`, тайм-аут - 5 секунд, тело - до 1 МиБ.
Другой адрес задаётся одинаковыми `--host` и `--port` у сервера и клиента.
Формат запроса и ответа: 5 байт длины JSON в big-endian, 1 байт операции,
JSON в UTF-8. Запуск сервера также доступен через `run.bat` или `sh run.sh`.

## Проверки

```powershell
py -B -m unittest discover -s tests -v
```

Ожидается `OK`. Тесты запускают свои серверы; вручную запускать сервер не нужно.
Для проверки оформления:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m flake8 src tests --max-line-length=80
```

При успешной проверке flake8 ничего не выводит. Сборка проекта не требуется.
