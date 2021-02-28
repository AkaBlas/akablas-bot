#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The module contains functionality for pausing weeks."""
import datetime as dtm
from typing import cast, Union, Match, Set

from ptbcontrib.roles import Role, RolesHandler
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
)
from telegram.ext import (
    CallbackContext,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
)

from bot.constants import (
    PAUSED_KEY,
    PAUSED_WEEKS_KEY,
    PAUSE_BUTTON,
    PAUSE_NAVIGATION_BUTTON,
    PAUSE_NAVIGATION_DONE,
    PAUSE_BUTTON_PATTERN,
    PAUSE_NAVIGATION_BUTTON_PATTERN,
)
from bot.utils import next_tuesday, iter_tuesdays, pprint, str2bool, parse_pprint

SELECTING_STATE = 'selecting_weeks_state'
SELECTION_TEXT = (
    'Bitte wähle aus, an welchen Dienstagen eine Probe stattfindet. Wenn Du fertig bist, '
    'klicke auf »Fertig«.'
)


def build_keyboard(start_date: dtm.date, context: CallbackContext) -> InlineKeyboardMarkup:
    """
    Builds the keyboard to be displayed for pausing weeks.

    Args:
        start_date (:obj:`datetime.date`): The date of the first tuesday to be displayed.
        context (:class:`telegram.ext.CallbackContext`): The context as provided by the dispatcher.

    Returns:
        :class:`telegram.InlineKeyboardMarkup`: The keyboard.
    """
    paused_weeks = cast(Set[dtm.date], context.bot_data[PAUSED_WEEKS_KEY])
    buttons = []
    for tuesday in iter_tuesdays(start_date, start_date + dtm.timedelta(days=5 * 7)):
        paused = tuesday in paused_weeks
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f'{pprint(tuesday)} {"⏸" if paused else "▶️"}',
                    callback_data=PAUSE_BUTTON.format(tuesday.isoformat(), not paused),
                )
            ]
        )
    navigation_buttons = []
    previous = start_date - dtm.timedelta(days=7 * 5)
    nxt = start_date + dtm.timedelta(days=7 * 5)
    if previous > dtm.date.today():
        navigation_buttons.append(
            InlineKeyboardButton(
                text='« Zurück', callback_data=PAUSE_NAVIGATION_BUTTON.format(previous.isoformat())
            )
        )

    navigation_buttons.append(
        InlineKeyboardButton(
            text='Weiter »', callback_data=PAUSE_NAVIGATION_BUTTON.format(nxt.isoformat())
        )
    )
    buttons.append(navigation_buttons)
    buttons.append([InlineKeyboardButton(text='Fertig ✔️', callback_data=PAUSE_NAVIGATION_DONE)])

    return InlineKeyboardMarkup(buttons)


def start(update: Update, context: CallbackContext) -> Union[str, int]:
    """
    Starts the conversation and asks the user to go to inline mode to select the instrument.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the dispatcher.

    Returns:
        The next state.
    """
    message = cast(Message, update.effective_message)
    paused = cast(Union[bool, dtm.date], context.bot_data[PAUSED_KEY])
    if paused:
        message.reply_text(
            'Aktuell finden keine Problem statt. Bitte versuch es noch einmal, wenn es wieder '
            'Probem gibt.'
        )
        return ConversationHandler.END

    reply_markup = build_keyboard(next_tuesday(dtm.date.today(), allow_today=False), context)

    message.reply_text(SELECTION_TEXT, reply_markup=reply_markup)
    return SELECTING_STATE


def parse_week_selection(update: Update, context: CallbackContext) -> str:
    """
    Parses the users selection of a week to (un-)pause and updates the keyboard.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the dispatcher.

    Returns:
        The next state.
    """
    match = cast(Match, context.match)
    message = cast(Message, update.effective_message)
    keyboard = cast(InlineKeyboardMarkup, message.reply_markup)

    selected_tuesday = dtm.date.fromisoformat(match.group(1))
    paused = str2bool(match.group(2))
    paused_weeks = cast(Set[dtm.date], context.bot_data[PAUSED_WEEKS_KEY])
    if paused:
        paused_weeks.add(selected_tuesday)
    else:
        paused_weeks.discard(selected_tuesday)

    first_tuesday = parse_pprint(keyboard.inline_keyboard[0][0].text.split()[0])
    reply_markup = build_keyboard(first_tuesday, context)
    message.edit_text(text=SELECTION_TEXT, reply_markup=reply_markup)
    return SELECTING_STATE


def navigate_weeks(update: Update, context: CallbackContext) -> str:
    """
    Parses the users selection for navigating weeks and updates the message accordingly.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the dispatcher.

    Returns:
        The next state.
    """
    selected_tuesday = dtm.date.fromisoformat(cast(Match, context.match).group(1))
    message = cast(Message, update.effective_message)
    reply_markup = build_keyboard(selected_tuesday, context)
    message.edit_text(text=SELECTION_TEXT, reply_markup=reply_markup)
    return SELECTING_STATE


def finish_pausing_weeks(update: Update, _: CallbackContext) -> int:
    """
    Ends the pausing of weeks.

    Args:
        update: The Telegram update.
        _: The callback context as provided by the dispatcher.

    Returns:
        The next state.
    """
    cast(Message, update.effective_message).edit_text('Alles klar, ist notiert. 🤓')
    return ConversationHandler.END


def build_pause_weeks_conversation(board_role: Role) -> ConversationHandler:
    """
    Builds the :class:`telegram.ext.ConversationHandler` to pause specific weeks. Will only be
    available to the :attr:`bot.constants.BOARD_ROLE` role.

    Args:
        board_role: The :attr:`bot.constants.BOARD_ROLE` role.

    """
    return ConversationHandler(
        entry_points=[RolesHandler(CommandHandler('proben_aussetzen', start), roles=board_role)],
        states={
            SELECTING_STATE: [
                CallbackQueryHandler(parse_week_selection, pattern=PAUSE_BUTTON_PATTERN),
                CallbackQueryHandler(navigate_weeks, pattern=PAUSE_NAVIGATION_BUTTON_PATTERN),
                CallbackQueryHandler(finish_pausing_weeks, pattern=PAUSE_NAVIGATION_DONE),
            ],
        },
        conversation_timeout=60,
        fallbacks=[],
    )
