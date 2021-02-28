#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The module contains functionality for basic commands and functionality."""
import datetime as dtm
import time
from typing import cast, Union, Literal, Set

from ptbcontrib.roles import BOT_DATA_KEY, Roles
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Message
from telegram.error import RetryAfter
from telegram.ext import CallbackContext

from bot.constants import USER_GUIDE, PAUSED_KEY, PAUSED_WEEKS_KEY, WATCHER_ROLE, BOARD_ROLE
from bot.utils import next_sweep_text, iter_tuesdays, next_tuesday, previous_tuesday


def info(update: Update, _: CallbackContext) -> None:
    """
    Returns some info about the bot.

    Args:
        update: The Telegram update.
        _: The callback context as provided by the dispatcher.
    """
    text = (
        'Hi! Ich bin der <b>AkaBlas Bot</b> und hier, um den Vorstand der AkaBlas zu unterstützen.'
        ' Falls Du nicht im Vorstand oder vom Vorstand autorisiert bist, werde ich Dich ignorieren'
        ' müssen ...'
        '\n\nFür mehr Details, besuche mich doch auf meiner Homepage 🙂.'
    )

    keyboard = InlineKeyboardMarkup.from_column(
        [
            InlineKeyboardButton('Anleitung 🤖', url=USER_GUIDE),
            InlineKeyboardButton('AkaBlas e.V. 🎶', url='https://akablas.de'),
        ]
    )

    cast(Message, update.effective_message).reply_text(text, reply_markup=keyboard)


def next_sweep(update: Update, context: CallbackContext) -> None:
    """
    Tells the user who's turn on cleaning the rehearsal room it is on the upcoming tuesday and the
    one after.

    Args:
        update: The incoming Telegram Update.
        context: The callback context as provided by the dispatcher.

    """
    cast(Message, update.effective_message).reply_text(next_sweep_text(context))


def pause_unpause(update: Update, context: CallbackContext) -> None:
    """
    Pauses or unpauses the bot. Informs the user about the result.

    Args:
        update: The incoming Telegram Update.
        context: The callback context as provided by the dispatcher.

    """
    message = cast(Message, update.effective_message)
    paused = cast(Union[Literal[False], dtm.date], context.bot_data[PAUSED_KEY])
    if not paused:
        context.bot_data[PAUSED_KEY] = dtm.date.today()
        message.reply_text('Proben pausiert. Die wöchtentlichen Nachrichten werden ausgesetzt.')
        return

    paused_weeks = cast(Set[dtm.date], context.bot_data[PAUSED_WEEKS_KEY])
    context.bot_data[PAUSED_KEY] = False
    paused_weeks |= set(iter_tuesdays(next_tuesday(paused), previous_tuesday(dtm.date.today())))

    swipe_text = next_sweep_text(context)
    message.reply_text(
        f'Probem werden fortgesetzt. Die wöchentlichen Nachrichten werden wieder gesendet. '
        f'Mit Fegen sind dran:\n\n{swipe_text}'
    )


def weekly_job(context: CallbackContext) -> None:
    """
    If not currently paused, sends a message to all groups in the :attr:`bot.constants.BOARD_ROLE`
    and :attr:`bot.constants.WATCHER_ROLE` roles

    Args:
        context: The callback context as provided by the dispatcher.

    """
    paused = cast(Union[bool, dtm.date], context.bot_data[PAUSED_KEY])
    if paused or dtm.date.today() in cast(Set[dtm.date], context.bot_data[PAUSED_WEEKS_KEY]):
        return

    text = next_sweep_text(context)
    roles = cast(Roles, context.bot_data[BOT_DATA_KEY])
    chat_ids = roles[WATCHER_ROLE].chat_ids | roles[BOARD_ROLE].chat_ids
    for group in (chat_id for chat_id in chat_ids if chat_id < 0):
        try:
            context.bot.send_message(chat_id=group, text=text)
            # Very low level flood control.
            # Should to the trick, as we're not expecting much traffic
            time.sleep(0.2)
        except RetryAfter as exc:
            # Still, just to be sure
            time.sleep(exc.retry_after + 1)
            context.bot.send_message(chat_id=group, text=text)
        except Exception as exc:  # pylint: disable=W0703
            try:
                context.dispatcher.dispatch_error(update=None, error=exc)
            except Exception:  # pylint: disable=W0703
                pass
