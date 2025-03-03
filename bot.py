"""Initialize everything and run the application.
"""
from core.logger import LOG_LEVELS, log
from core.wiki import Wiki
from core.modules import ModuleLoader
import config

from typing import MutableMapping, List, Any
from prettytable import PrettyTable
from core.utils import Periodic
import argparse
import asyncio
import sys
import os


def get_argparser() -> argparse.ArgumentParser:
    """Get argument parser

    Returns:
      argparse.ArgumentParser: Argument parser

    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="print bot version - will not run the bot",
    )
    parser.add_argument(
        "-m",
        "--modules",
        action="store_true",
        help="print module list - will not run the bot",
    )
    parser.add_argument(
        "--logging_level",
        choices=list(LOG_LEVELS),
        help="the level to use for logging - defaults to INFO",
        default="INFO",
    )

    return parser


class Bot:
    """Cerberus.aic bot class

    Attributes:
        config (MutableMapping[str, Any]): Bot config
        _wiki (Wiki): Wiki class
    """

    config: MutableMapping[str, Any] = config.load_config("bot")
    _wiki: Wiki = Wiki(config.get("site", "https://scpfoundation.net")).auth(os.getenv("CERBERUS_AUTHKEY"))

    def run(self) -> int:
        """Run bot and all modules

        Returns:
          int: Exit code

        """
        log.info("Initializing \"Cerberus.aic\"")
        print(os.getenv("CERBERUS_AUTHKEY"))

        log.info("Load all modules...")
        module_loader = ModuleLoader(self._wiki)
        module_loader.load_modules()

        log.info("Start all modules...")
        module_loader.start_modules()

        loop = asyncio.get_event_loop()
        try:
            loop.create_task(self.main(list(module_loader.tasks)))
            loop.run_forever()
        except BaseException as ex:
            log.error(ex, exc_info=True)
        finally:
            loop.stop()

        log.info("Stop all modules...")
        module_loader.stop_modules()

        return 0

    @staticmethod
    async def main(tasks: List[Periodic]):
        """Run all periodic tasks from modules

        Args:
            tasks (List[Periodic]): List of periodic tasks
        """
        for task in tasks:
            await task.start()

    @classmethod
    def get_version(cls) -> str:
        """Get bot version

        Returns:
          str: Version

        """
        return cls.config["version"]

    @classmethod
    def modules_data(cls) -> PrettyTable:
        """Get modules data in pretty table

        Returns:
          PrettyTable: Pretty table with modules data

        """
        table = PrettyTable()
        table.field_names = ["Alias", "Description", "Author", "Version"]

        for module in ModuleLoader(cls._wiki).modules_data():
            table.add_row(
                [
                    module["__alias__"],
                    module["__description__"],
                    module["__author__"],
                    module["__version__"],
                ]
            )

        return table


def start():
    """Start Cerberus.aic with arguments
    """
    args = get_argparser().parse_args()

    log.setLevel(LOG_LEVELS[args.logging_level])

    if args.version:
        print(f"Bot version: v{Bot.get_version()}")
    elif args.modules:
        print(Bot.modules_data())
    else:
        bot = Bot()
        sys.exit(bot.run())
