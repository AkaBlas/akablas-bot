#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The module contains functions that register the handlers."""
import datetime as dtm
import warnings
from typing import cast

from ptbcontrib.roles import setup_roles, RolesHandler
from telegram.ext import (
    Dispatcher,
    CommandHandler,
    JobQueue,
    Filters,
    MessageHandler,
)

from bot.admin import (
    subscribe_unsubscribe,
    list_members,
    chat_migration,
    build_add_user_conversation_handler,
    build_kick_user_conversation_handler,
)
from bot.basic import info, next_sweep, weekly_job, pause_unpause
from bot.constants import BOARD_ROLE, WATCHER_ROLE, LAST_SWEEP_KEY, PAUSED_WEEKS_KEY, PAUSED_KEY
from bot.pauseweeks import build_pause_weeks_conversation
from bot.setnext import build_conversation
from bot.utils import next_tuesday

# B/C we know what we're doing
warnings.filterwarnings('ignore', message="If 'per_", module='telegram.ext.conversationhandler')
warnings.filterwarnings(
    'ignore',
    message="BasePersistence.insert_bot does not handle objects",
    module='telegram.ext.basepersistence',
)
warnings.filterwarnings(
    'ignore',
    message="BasePersistence.replace_bot does not handle objects",
    module='telegram.ext.basepersistence',
)


def setup_dispatcher(dispatcher: Dispatcher, admin: int) -> None:
    """
    Registers the different handlers, prepares ``chat/user/bot_data`` etc.

    Args:
        dispatcher: The dispatcher.
        admin: The admins Telegram chat ID.

    """
    # Set up roles
    roles = setup_roles(dispatcher)
    roles.add_admin(admin)
    if WATCHER_ROLE not in roles:
        roles.add_role(name=WATCHER_ROLE)
    if BOARD_ROLE not in roles:
        roles.add_role(name=BOARD_ROLE, child_roles=roles[WATCHER_ROLE])

    # Set up weekly job
    cast(JobQueue, dispatcher.job_queue).run_daily(weekly_job, time=dtm.time(20, 30), days=(1,))

    # Handle chat migration
    dispatcher.add_handler(MessageHandler(Filters.status_update.migrate, chat_migration))

    # Handlers
    dispatcher.add_handler(CommandHandler(['start', 'info', 'help', 'hilfe'], info))
    dispatcher.add_handler(
        RolesHandler(CommandHandler('fegen', next_sweep), roles=roles[WATCHER_ROLE])
    )
    dispatcher.add_handler(
        RolesHandler(
            CommandHandler('pausieren_umschalten', pause_unpause), roles=roles[BOARD_ROLE]
        )
    )
    dispatcher.add_handler(
        RolesHandler(
            CommandHandler(
                'gruppenrechte_aendern', subscribe_unsubscribe, filters=Filters.chat_type.groups
            ),
            roles=roles[BOARD_ROLE],
        )
    )
    dispatcher.add_handler(
        RolesHandler(CommandHandler('nutzer_anzeigen', list_members), roles=roles[BOARD_ROLE])
    )

    dispatcher.add_handler(build_conversation(roles[BOARD_ROLE]))
    dispatcher.add_handler(build_add_user_conversation_handler(roles[BOARD_ROLE]))
    dispatcher.add_handler(build_kick_user_conversation_handler(roles[BOARD_ROLE]))
    dispatcher.add_handler(build_pause_weeks_conversation(roles[BOARD_ROLE]))

    # prepare bot_data
    dispatcher.bot_data.setdefault(LAST_SWEEP_KEY, (next_tuesday(dtm.date.today()), 0))
    dispatcher.bot_data.setdefault(PAUSED_WEEKS_KEY, set())
    dispatcher.bot_data.setdefault(PAUSED_KEY, False)

    # Set commands
    dispatcher.bot.set_my_commands(
        [
            ('fegen', 'Wer ist mit Fegen dran?'),
            ('setze_naechsten', 'Nächstes Register setzen'),
            ('pausieren_umschalten', 'Proben pausieren/forsetzen'),
            ('proben_aussetzen', 'Bestimmte Proben aussetzen'),
            ('gruppenrechte_aendern', 'Erlaubt/Verbietet den Bot in der Gruppe'),
            ('nutzer_hinzufuegen', 'Neuen Nutzer hinzufügen/hochstufen'),
            ('nutzer_entfernen', 'Nutzer entfernen'),
            ('nutzer_anzeigen', 'Zeigt die authorisierten Nutzer des Bots'),
            ('hilfe', 'Allgemeine Informationen'),
        ]
    )
