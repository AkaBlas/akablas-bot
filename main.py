#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The script that runs the bot."""
import logging
from configparser import ConfigParser
from telegram import ParseMode
from telegram.ext import Updater, Defaults, PicklePersistence

from bot.constants import TIMEZONE
from bot.setup import setup_dispatcher  # type: ignore[attr-defined]

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING,
    # filename='abb.log',
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Start the bot."""
    # Read configuration values from bot.ini
    config = ConfigParser()
    config.read('bot.ini')
    token = config['yourls-bot']['token']
    admin = int(config['yourls-bot']['admins_chat_id'])

    # Create the Updater and pass it your bot's token.
    defaults = Defaults(
        parse_mode=ParseMode.HTML,
        disable_notification=True,
        disable_web_page_preview=True,
        tzinfo=TIMEZONE,
    )
    persistence = PicklePersistence(filename='abb.db', single_file=False)
    updater = Updater(token, defaults=defaults, persistence=persistence)
    setup_dispatcher(dispatcher=updater.dispatcher, admin=admin)

    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
