Первый этап — модель данных

Участники, команды и ответы хранятся в памяти. Можно создавать записи,
получать все записи или одну по id, выполнять выборку за последние 8 минут.

py -m src.demo - показывает все операции первого этапа и ожидаемые ошибки.

py -m src.repl - открывает интерактивную модель.

data = {"ip": "127.0.0.1", "locale": "ru-RU", "user_agent": "Firefox"} - задаёт данные участника после появления >>>.

participant = model.create_participant(data) - создаёт участника в памяти.

model.get_participants() - показывает участников в консоли модели.

model.get_participant(participant["id"]) - получает созданного участника по id.

model.get_recent_results() - показывает выборку по формуле.

model.get_participant(-1) - показывает ошибку отсутствующего участника.

exit() - закрывает интерактивную консоль.

Второй этап — удалённые вызовы по TCP

Клиент вызывает те же 10 методов на сервере. Сервер хранит данные в памяти
и записывает успешные ответы и ошибки в journal.log.

py -m src.server - запускает сервер в первом терминале; оставить работающим.

py -m src.rpc_demo - показывает все 10 удалённых методов во втором терминале.

py -m src.client - открывает интерактивный клиент во втором терминале.

data = {"ip": "127.0.0.1", "locale": "ru-RU", "user_agent": "Firefox"} - задаёт данные участника после появления >>>.

participant = client.create_participant(data) - создаёт участника на сервере через TCP.

client.get_participants() - показывает участников в консоли клиента.

client.get_participant(participant["id"]) - получает созданного участника с сервера по id.

client.get_recent_results() - получает выборку по формуле через TCP.

client.get_participant(-1) - показывает ошибку отсутствующего участника.

exit() - закрывает интерактивный клиент.

Get-Content journal.log -Encoding utf8 - показывает журнал в PowerShell.

Ctrl+C - останавливает сервер в первом терминале.

py -B -m unittest discover -s tests -v - запускает тесты обоих этапов.

.venv\Scripts\python.exe -m flake8 src tests --max-line-length=80 - проверяет оформление кода.
