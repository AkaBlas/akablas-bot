#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The module contains functionality for changing the order of instrument groups."""
import datetime as dtm
from typing import cast, Union, List, Set

from rapidfuzz import process
from ptbcontrib.roles import Role, RolesHandler
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    InlineQuery,
    ChosenInlineResult,
    User,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.ext import (
    CallbackContext,
    ConversationHandler,
    CommandHandler,
    InlineQueryHandler,
    ChosenInlineResultHandler,
    Filters,
    MessageHandler,
)

from bot.constants import (
    PAUSED_KEY,
    PAUSED_WEEKS_KEY,
    INSTRUMENTS,
    LAST_SWEEP_KEY,
)
from bot.utils import next_tuesday, iter_tuesdays, pprint

SELECTING = 'selecting_state'
PARSING_SELECTION = 'parsing_selection'


def inline_query_results(
    instruments: Union[List[str], str] = None
) -> List[InlineQueryResultArticle]:
    """
    Builds a list of :class:`telegram.InlineQueryResultArticle` to show as reply to an inline
    query. The IDs will be the index of the instrument groups in :attr:`INSTRUMENTS`.

    Args:
        instruments: Pass to only allow the specified instruments. Must be a subset of
            :attr:`INSTRUMENTS`.

    """
    if instruments is None:
        effective_instruments = INSTRUMENTS
    elif isinstance(instruments, str):
        effective_instruments = [instruments]
    else:
        effective_instruments = instruments

    return [
        InlineQueryResultArticle(
            id=str(INSTRUMENTS.index(instrument)),
            title=instrument,
            input_message_content=InputTextMessageContent(instrument),
        )
        for instrument in effective_instruments
    ]


def start(update: Update, context: CallbackContext) -> Union[str, int]:
    """
    Starts the conversation and asks the user to go to inline mode to select the instrument.

    Args:
        update: The Telegram update.
        context: The callback context as provided by the dispatcher.
    """
    message = cast(Message, update.effective_message)
    paused = cast(Union[bool, dtm.date], context.bot_data[PAUSED_KEY])
    if paused:
        message.reply_text(
            'Aktuell finden keine Problem statt. Bitte komm zurück, wenn es wieder Probem gibt.'
        )
        return ConversationHandler.END

    paused_weeks = cast(List[dtm.date], context.bot_data[PAUSED_WEEKS_KEY])
    next_td = next_tuesday(dtm.date.today(), allow_today=False)
    if next_td not in paused_weeks:
        effective_date = next_td
    else:
        candidates = [
            td
            for td in iter_tuesdays(min(paused_weeks), max(paused_weeks))
            if td not in paused_weeks
        ]
        candidates.append(next_tuesday(max(paused_weeks)))
        effective_date = min(candidates)

    text = (
        f'Um für den <b>{pprint(effective_date)}</b> eine bestimmet Instrumentengruppe zu '
        f'bestrafen, klicke bitte auf den Knopf unten und suche Dir ein Register aus.\n\n'
        f'Um abzubrechen, sage einfach /abbruch.'
    )
    keyboard = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton('Klick mich! 👆', switch_inline_query_current_chat='')
    )

    message.reply_text(text, reply_markup=keyboard)
    return SELECTING


def offer_section(update: Update, _: CallbackContext) -> str:
    """
    Shows the user a list of available instrument groups. If there is an inline query, the nearest
    match is extracted with fuzzy matching.

    Args:
        update: The incoming Telegram Update.
        _: The callback context as provided by the dispatcher.

    """
    inline_query = cast(InlineQuery, update.inline_query)
    query = inline_query.query.strip()
    instruments = process.extractOne(query, INSTRUMENTS)[0] if query else None
    inline_query.answer(
        results=inline_query_results(instruments),  # type: ignore[arg-type]
        auto_pagination=True,
        cache_time=0,
    )
    return PARSING_SELECTION


def parse_selection(update: Update, context: CallbackContext) -> int:
    """
    Parses the chosen instrument groups and saves the setting.

    Args:
        update: The incoming Telegram Update.
        context: The callback context as provided by the dispatcher.

    """
    chosen_inline_result = cast(ChosenInlineResult, update.chosen_inline_result)
    chosen_idx = int(chosen_inline_result.result_id)
    nxt_td = next_tuesday(dtm.date.today(), allow_today=False)
    context.bot_data[LAST_SWEEP_KEY] = (
        nxt_td,
        chosen_idx,
    )
    cast(User, update.effective_user).send_message('Ist notiert! ✍️')

    paused_weeks = cast(Set, context.bot_data[PAUSED_WEEKS_KEY])
    for tuesday in paused_weeks.copy():
        if tuesday < nxt_td:
            paused_weeks.discard(tuesday)

    return ConversationHandler.END


def abort(update: Update, _: CallbackContext) -> int:
    """
    Abort the conversation.

    Args:
        update: The incoming Telegram Update.
        _: The callback context as provided by the dispatcher.

    """
    cast(User, update.effective_user).send_message('Vorgang abgebrochen.')
    return ConversationHandler.END


def build_conversation(board_role: Role) -> ConversationHandler:
    """
    Builds the :class:`telegram.ext.ConversationHandler` to set the instrument group for the next
    sweep.

    Args:
        board_role: The :attr:`bot.constants.BOARD_ROLE` role.

    """
    return ConversationHandler(
        entry_points=[RolesHandler(CommandHandler('setze_naechsten', start), roles=board_role)],
        states={
            SELECTING: [InlineQueryHandler(offer_section)],
            PARSING_SELECTION: [ChosenInlineResultHandler(parse_selection)],
            ConversationHandler.TIMEOUT: [
                MessageHandler(Filters.all, abort),
                InlineQueryHandler(abort),
            ],
        },
        per_chat=False,  # b/c InlineQuery/ChoseInlineResult don't have an effective chat
        conversation_timeout=60,
        fallbacks=[CommandHandler('abbruch', abort)],
    )
