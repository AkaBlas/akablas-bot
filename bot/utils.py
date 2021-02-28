#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The module contains functionality for changing the order of instrument groups."""
import datetime as dtm
from typing import cast, Tuple, Iterator, Union, Literal, Set

from telegram import Chat, Bot, TelegramError
from telegram.ext import CallbackContext

from bot.constants import TIMEZONE, PAUSED_KEY, PAUSED_WEEKS_KEY, LAST_SWEEP_KEY, INSTRUMENTS


def pprint(date: dtm.date) -> str:
    """
    Thin wrapper for :meth:`datetime.date.strftime` to achieve consistent formatting.

    Args:
        date: The date to format.

    """
    return date.strftime("%d.%m.%y")


def parse_pprint(date: str) -> dtm.date:
    """
    Reverse operation for :meth:`pprint`.

    Args:
        date: The date to format.

    """
    return dtm.datetime.strptime(date, "%d.%m.%y").date()


def rehearsal_time(date: dtm.date) -> dtm.time:
    """
    Gives the rehearsal time (7:30 pm) as :obj:`datetime.time` object localized as
    :attr:`bot.utils.TIMEZONE`.

    Args:
        date: The date.

    """
    return TIMEZONE.localize(dtm.datetime.combine(date, dtm.time(19, 30))).timetz()


def next_tuesday(date: dtm.date, allow_today: bool = True) -> dtm.date:
    """
    Gives the date of the tuesday following the given datetime.

    Args:
        date: The date to compute the next tuesday for.
        allow_today: If :obj:`True`, the return value may be the same date as the input value.
            Otherwise the next week is forced. Defaults to :obj:`True`.

    Returns:
        obj:`datetime.date`: The date of the next tuesday
    """
    days_ahead = 1 - date.weekday()
    # Target day already happened this week
    if (allow_today and days_ahead < 0) or (not allow_today and days_ahead <= 0):
        days_ahead += 7
    return date + dtm.timedelta(days_ahead)


def previous_tuesday(date: dtm.date, allow_today: bool = True) -> dtm.date:
    """
    Gives the date of the tuesday before the given datetime.

    Args:
        date: The date to compute the next tuesday for.
        allow_today: If :obj:`True`, the return value may be the same date as the input value.
            Otherwise the next week is forced. Defaults to :obj:`True`.

    Returns:
        obj:`datetime.date`: The date of the previous tuesday
    """
    next_td = next_tuesday(date=date, allow_today=allow_today)
    return next_td if (next_td == date and allow_today) else next_td + dtm.timedelta(days=-7)


def iter_tuesdays(from_date: dtm.date, until_date: dtm.date) -> Iterator[dtm.date]:
    """
    Gives an iterator allowing to iterate over the tuesdays from :attr:`from_date` to
    :attr:`until_date`. Both dates must be tuesdays.

    Note:
        Just like for :meth:`range`, :attr:`until_date` will be *not* be included!

    Args:
        from_date: The start date.
        until_date: The end date.

    """
    if (from_date.weekday(), until_date.weekday()) != (1, 1):
        ValueError('Both input dates must be tuesdays.')
    current_date = from_date
    while current_date < until_date:
        yield current_date
        current_date = next_tuesday(current_date, allow_today=False)


def next_sweep_text(context: CallbackContext, html: bool = True) -> str:
    """
    Tells you, whe needs to sweep this week an next.

    Args:
        context: The context as provided by the dispatcher.
        html: Whether or not to make the output HTML-formatted as expected by
            :meth:`telegram.Bot.send_message`. Defaults to :obj:`True`.
    """
    if cast(Union[bool, dtm.date], context.bot_data[PAUSED_KEY]):
        return 'Aktuell finden keine Proben statt. Es muss nicht gefegt werden.'

    paused_weeks = cast(Set[dtm.date], context.bot_data[PAUSED_WEEKS_KEY])
    init_date, last_idx = cast(Tuple[dtm.date, int], context.bot_data[LAST_SWEEP_KEY])

    today = dtm.date.today()
    tuesday = next_tuesday(today)
    number_paused_weeks = sum(td not in paused_weeks for td in iter_tuesdays(init_date, tuesday))
    weeks_passed = last_idx + min((tuesday - init_date).days, 0) / 7 - number_paused_weeks

    if tuesday in paused_weeks:
        current = 'Keine Probe.'
    else:
        current = INSTRUMENTS[int(weeks_passed % len(INSTRUMENTS))]

    next_td = tuesday + dtm.timedelta(7)
    if next_td in paused_weeks:
        next_week = 'Keine Probe.'
    else:
        next_weeks_passed = weeks_passed + 1 if tuesday not in paused_weeks else weeks_passed
        next_week = INSTRUMENTS[int(next_weeks_passed % len(INSTRUMENTS))]

    current_text = f'<b>{current}</b>' if html else current
    next_week_text = f'<b>{next_week}</b>' if html else next_week

    return (
        f'Kommenden Dienstag ({pprint(tuesday)}) - {current_text}\nNächsten Dienstag '
        f'({pprint(next_td)}) - {next_week_text}'
    )


def str2bool(str_input: Literal['True', 'False']) -> bool:
    """
    Shortcut for converting ``str(boolean_input)`` back to a boolean.

    Args:
        str_input: The input.
    """
    return str_input == 'True'


def chat2str(chat_id: Union[str, int], bot: Bot) -> str:
    """
    Given a chat id, returns a string representation of the chat as combination of first name,
    last name, username and chat title.

    In case fetching the chat via :meth:`telegram.Bot.get_chat` fails, the output is
    ``f'Chat-ID {chat_id}'``.

    Args:
        chat_id: The chat id.
        bot: The bot.

    Returns:
        str: The string representation.

    """
    try:
        chat = bot.get_chat(chat_id)
        if chat.type == Chat.PRIVATE:
            name = (
                f'{chat.first_name} {chat.last_name}'
                if chat.last_name
                else cast(str, chat.first_name)
            )
        else:
            name = cast(str, chat.title)
        if chat.username:
            name = f'{name} (@{chat.username})'
    except TelegramError:
        name = f'Chat-ID {chat_id}'

    return name
