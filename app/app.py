from internal.decorations.decorator import KaliDecoratorNaMinimalkax
from internal.downloader import Downloader
from sys import argv


class App:
    @staticmethod
    def get_params():
        args = argv
        # print(args)
        if len(args) != 3:
            return None, None
        return args[1], args[2]

    def __init__(self):
        kali_decorator = KaliDecoratorNaMinimalkax()
        self._downloader = Downloader(kali_decorator)

    async def run(self):
        await self._downloader.run()
