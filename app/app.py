from internal.downloader import Downloader
from internal.mount import Mount
import logging

class App:

    DOWNLOAD_DIR = "downloads"

    def __init__(self):
        logger = logging.getLogger(__name__)
        logging.basicConfig(format='%(asctime)s :: %(levelname)s :: %(message)s', level=logging.INFO)

        self._downloader = Downloader(logger, self.DOWNLOAD_DIR)
        self._mount = Mount(logger, self.DOWNLOAD_DIR)

    async def run(self):
        await self._downloader.run()
        self._mount.run()