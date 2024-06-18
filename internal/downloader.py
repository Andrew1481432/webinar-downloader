import asyncio
from datetime import datetime
import json

import httpx
from anyio.streams.file import FileWriteStream
from internal.decorations.decorator import Decorator

import requests

class Downloader:
    DOWNLOAD_DIR = "downloads"

    SKIP_MODULES = [
        "conference.add",
        "conference.delete",
        "eventsession.stop",
        "screensharing.stream.delete",
        "mediasession.update",
        "screensharing.update",
        "userlist.offline",
        "userlist.online",
        "conference.update",
        "conference.stream.delete",
        "eventSession.raisingHand.lowered",
        "eventSession.raisingHand.raised",
    ]

    def __init__(self, decorator: Decorator = Decorator()):
        self._decorator = decorator

    def fetch_event_data(self, event_id):
        params = {
            "withoutCuts": "false"
        }
        response = requests.get(
            f"https://events.webinar.ru/api/eventsessions/{event_id}/record",
            params=params,
        )
        data = response.json()
        return data

    def process_mediasession(self, mediasession, start_time):
        media_type = list(mediasession["stream"].keys())[1] + ".mp4"
        time = mediasession["time"] - start_time
        url = mediasession["url"]
        return time, media_type, url

    def process_message(self, message, start_time):
        create_at = datetime.strptime(
            message["createAt"], "%Y-%m-%dT%H:%M:%S%z"
        ).timestamp()
        time = create_at - start_time
        author_name = message["authorName"]
        text = message["text"]
        return time, author_name, text

    def process_event_logs(self, event_logs):
        urls = []
        messages = []
        files = []
        start_time = event_logs.pop(0)["time"]

        for event in event_logs:
            data = event["data"]
            module = event["module"]

            if module in self.SKIP_MODULES:
                continue

            if module == "cut.end":
                mediasession = event["snapshot"]["data"]["mediasession"]
                urls.extend(self.process_mediasession(x, start_time) for x in mediasession)
                message = event["snapshot"]["data"]["message"]
                messages.extend(self.process_message(x, start_time) for x in message)
                continue

            match module:
                case "message.add":
                    messages.append(self.process_message(data, start_time))
                case "mediasession.add":
                    urls.append(self.process_mediasession(data, start_time))
                case "presentation.update":
                    reference = data["fileReference"]

                    if "slide" in reference:
                        slide = reference["slide"]
                        urls.append((event["time"] - start_time, "slide.jpg", slide["url"]))
                    file = reference["file"]
                    files.append((file["name"], file["url"]))
                # case _:
                # print(event)

        return urls, messages, files

    def dump(self, data):
        with open(f"{self.DOWNLOAD_DIR}/dump.json", "w") as f:
            json.dump(data, f, sort_keys=True, indent=4,
                      ensure_ascii=False)

    def save_chat(self, min_value, messages):
        messages = [(int(max(row[0] - min_value, 0)), row[1], row[2]) for row in
                    list({tuple(t): t for t in messages}.values())]

        with open(f"{self.DOWNLOAD_DIR}/chat.txt", "w") as f:
            for message in messages:
                f.write(f"{str(message)}\n")

    async def download_file(self, path, url, client):
        print(f"Старт {path}")
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            async with await FileWriteStream.from_path(path) as stream:
                async for chunk in response.aiter_bytes():
                    await stream.send(chunk)
        print(f"Файл {path} загружен успешно.")

    async def download_chunks(self, urls, files):
        async with httpx.AsyncClient(timeout=600) as client:
            tasks = [
                asyncio.create_task(
                    self.download_file(f"{self.DOWNLOAD_DIR}/{time}_{media_type}", url, client)
                )
                for time, media_type, url in urls
            ]

            tasks.extend(
                [
                    asyncio.create_task(
                        self.download_file(f"{self.DOWNLOAD_DIR}/FILE_{name}", url, client)
                    )
                    for name, url in files
                ]
            )
            await asyncio.gather(*tasks)

    async def run(self):
        print("Program started...")

        print(
            "Введите ссылку вебинара (пример: https://events.webinar.ru/j/21390906/100137538/record-new/1122397272) Важно без слеша в конце. Вообще нужен просто последний год, можно и его ввести"
        )

        try:
            event_id = int(input("Ссылка: ").split("/")[-1])
            data = self.fetch_event_data(event_id)

            self.dump(data)

            event_logs = data["eventLogs"]

            urls, messages, files = self.process_event_logs(event_logs)
            urls = list(set(urls))

            min_value = min(row[0] for row in urls)
            self.save_chat(min_value, messages)

            files = list(set(files))
            urls = [(row[0], row[1], row[2]) for row in urls]
            await self.download_chunks(urls, files)

        except KeyboardInterrupt:
            print()
            exit(0)
        except EOFError:
            print()
            exit(0)
