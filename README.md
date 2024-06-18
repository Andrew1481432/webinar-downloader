# webinar-downloader

1. Создание вирутального окружения `python -m venv env`
2. Активация виртуального окружения `source env/bin/activate`
3. Установка зависимостей `pip install -r requirements.txt`
4. Запуск `python download_webinar.py`
5. Вводим ссылку на вебинар или последнее число в ссылке ![image](https://github.com/vladdd183/webinar-downloader/assets/26278260/a340bdc3-221c-4fcc-8124-4d0efb93a39f)

### Скачивание

Скрипт создает папку downloads куда сохраняет полученные чанки, сохраняются под именем (время от начала)_(тип видео).mp4
Время от начало ведется с самого первого аудио-видео клипа (сделано для того, чтобы не создавать время тишины, когда вебинар начался, люди пишут, а админ ещё не начал ничего показывать/говорить)
Тип видео в данный момент 4:
- screensharing (демонстрация экрана) с указанием времени
- conference (вебка) с указанием времени
- Слайд (jpg) с указанием времени
- Файл (FILE_) в основном слайды берутся из вордовских файлов, их тоже можно скачивать, они сохраняются в downloads с префиксом FILE_(название файла) без указания времени
![image](https://github.com/vladdd183/webinar-downloader/assets/26278260/5d617aed-c2f6-4a4f-8576-8ad0d3ba1ab2)

На скрине выше можно видеть в самом низу по центру видео-файл, но без превью: это аудио-файл, без видео (когда не включена вебка, или вебинар баганул)

Скрипт создает файл chat.txt в нем хранятся сообщения чата и время отправки в секундах сначала вебинара (начала вебинара считается от первого видео-аудио файла, это значит, что сообщения написанные раньше этого момента будут иметь время отправки 0)

![image](https://github.com/vladdd183/webinar-downloader/assets/26278260/c42abef1-33db-4aad-96be-941646c5eee2)

### Монтирование

Монтирование производится с помощью утилиты `ffmpeg`.
Монтирование работает только на видео(слайды планируются в будущем).

На данный момент скрин-каст отображается в центре экрана, конференция (вебка) сбоку -- в общем компоновка как в оригинальном вебинаре.

Протестировано монтировавание. Монтирование работает отлично на видео, на которых у лектора не было проблем с интернетом и благодаря чему вебинар формировал небольшое кол-во чанков, на больших кол-вах может происходить черный экран/пропадать голос(в будущем постраемся исправить)...