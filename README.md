py -m src.demo - показывает работу первого этапа и ожидаемые ошибки.

py -m src.repl - открывает интерактивную модель первого этапа.

model.get_participants() - показывает участников в консоли модели.

model.get_recent_results() - показывает выборку по формуле в консоли модели.

exit() - закрывает интерактивную консоль.

py -m src.server - запускает сервер второго этапа в первом терминале.

py -m src.rpc_demo - показывает все 10 удалённых методов во втором терминале.

py -m src.client - открывает интерактивный клиент во втором терминале.

client.get_participants() - показывает участников в консоли клиента.

client.get_recent_results() - получает выборку по формуле через TCP.

Get-Content journal.log -Encoding utf8 - показывает журнал ответов в PowerShell.

Ctrl+C - останавливает сервер в первом терминале.

py -B -m unittest discover -s tests -v - запускает все тесты.

.venv\Scripts\python.exe -m flake8 src tests --max-line-length=80 - проверяет оформление кода.
