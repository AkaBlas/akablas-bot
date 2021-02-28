#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The module contains utility functionality for adding & removing users & groups to/from the
allowed users."""
from typing import cast, Match, List, Union

from ptbcontrib.roles import Roles, BOT_DATA_KEY, Role, RolesHandler
from telegram import (
    Update,
    Chat,
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    User,
    ChosenInlineResult,
    InlineQuery,
)
from telegram.ext import (
    CallbackContext,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
    InlineQueryHandler,
    ChosenInlineResultHandler,
    TypeHandler,
)

from bot.constants import (
    WATCHER_ROLE,
    USER_GUIDE,
    BOARD_ROLE,
    PROMOTE_USER,
    ADD_USER,
    PROMOTE_USER_PATTERN,
    ADD_USER_PATTERN,
)
from bot.utils import str2bool, chat2str

GET_UID_STATE = 'get_user_id'
SELECT_ROLE_STATE = 'select_role'
KICK_USER_STATE = 'kick_user'


def subscribe_unsubscribe(update: Update, context: CallbackContext) -> None:
    """
    Subscribes/Unsubscribes the group to the weekly messages by adding to to the
    :attr:`bot.constants.WATCHER_ROLE` role.

    Args:
        update: The incoming Telegram Update.
        context: The callback context as provided by the dispatcher.

    """
    watcher_role = cast(Roles, context.bot_data[BOT_DATA_KEY])[WATCHER_ROLE]
    chat_id = cast(Chat, update.effective_chat).id
    if chat_id in watcher_role.chat_ids:
        watcher_role.kick_member(chat_id)
        text = (
            'Diese Gruppe erhält keine wöchtentlichen Nachrichten mehr und kann auch den Befehl '
            '/fegen nicht mehr nutzen.'
        )
    else:
        watcher_role.add_member(chat_id)
        text = (
            'Diese Gruppe erhält nun jeden Dienstag eine Nachricht mit dem aktuellen Register und '
            'kann auch den Befehl /fegen nutzen.'
        )
    cast(Message, update.effective_message).reply_text(text)


def chat_migration(update: Update, context: CallbackContext) -> None:
    """
    Handles migration of groups to super groups by replacing the chat id in the roles if necessary.
    For completeness sake informs the group.

    Args:
        update: The incoming Telegram Update.
        context: The callback context as provided by the dispatcher.

    """
    message = cast(Message, update.effective_message)

    # Get old and new chat ids
    old_id = message.migrate_from_chat_id or message.chat_id
    new_id = message.migrate_to_chat_id or message.chat_id

    roles = cast(Roles, context.bot_data[BOT_DATA_KEY])
    inform = False
    for role_name in [WATCHER_ROLE, BOARD_ROLE]:
        role = roles[role_name]
        if old_id in role.chat_ids:
            role.kick_member(old_id)
            role.add_member(new_id)
            inform = True

    if inform:
        context.bot.send_message(
            chat_id=new_id,
            text=(
                'Nur zur Info: Diese Gruppe ist gerade zur Supergroup geworden. Ich habe die '
                'Änderung notiert. Es sollte weiterhin alles funktionieren.'
            ),
        )


def list_members(update: Update, context: CallbackContext) -> None:
    """
    Gives an overview over the :attr:`bot.constants.BOARD_ROLE` and
    :attr:`bot.constants.WATCHER_ROLE` roles.

    Args:
        update: The incoming Telegram Update.
        context: The callback context as provided by the dispatcher.

    """
    text = (
        'Die folgenden Nutzer und Gruppen sind Administratoren:\n\n{admins}\n\n'
        'Die folgenden Nutzer und Gruppen sind Zuschauer:\n\n{watchers}\n\n'
        'Was genau der Unterschied zwischen Administratoren und Zuschauern ist, steht in der '
        'Anleitung.'
    )
    keyboard = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton('Anleitung 🤖', url=USER_GUIDE),
    )

    roles = cast(Roles, context.bot_data[BOT_DATA_KEY])
    admins: List[str] = []
    watchers: List[str] = []
    for list_, chat_ids in [
        (admins, roles[BOARD_ROLE].chat_ids),
        (watchers, roles[WATCHER_ROLE].chat_ids),
    ]:
        list_.extend(chat2str(chat_id, context.bot) for chat_id in chat_ids)

    text = text.format(admins=', '.join(admins) or '-', watchers=', '.join(watchers) or '-')
    cast(Message, update.effective_message).reply_text(text=text, reply_markup=keyboard)


def timeout(update: Update, _: CallbackContext) -> None:
    """
    Informs the user that the current operation has timed out.

    Args:
        update: The incoming Telegram update.
        _: The context as provided by the :class:`telegram.ext.Dispatcher`.

    Returns:
        The next state.

    """
    if not update.effective_user:
        return
    update.effective_user.send_message('<i>Timeout!</i> Operation abgebrochen.')


def add_user_start(update: Update, _: CallbackContext) -> str:
    """
    Initializes the add user conversation and asks for the ID of the user to add.

    Args:
        update: The incoming Telegram update.
        _: The context as provided by the :class:`telegram.ext.Dispatcher`.

    Returns:
        The next state.

    """
    cast(Message, update.effective_message).reply_text(
        'Wer soll den Bot denn benutzen dürfen? Leite mir eine Nachricht des Nutzers weiter '
        'oder schicke mir seine Telegram ID.'
    )
    return GET_UID_STATE


def add_user_get_uid(update: Update, context: CallbackContext) -> Union[str, int]:
    """
    Tries to read the user ID.

    Args:
        update: The incoming Telegram update.
        context: The context as provided by the :class:`telegram.ext.Dispatcher`.

    Returns:
        The next state.

    """
    roles = cast(Roles, context.bot_data[BOT_DATA_KEY])
    message = cast(Message, update.effective_message)

    if message.forward_date:
        if not message.forward_from:
            message.reply_text(
                "Der Nutzer erlaubt anscheinend nicht, dass seine Kontaktdaten in "
                "weitergeleiteten  Nachrichten angezeigt werden. Deswegen kann ich die ID nicht "
                "auslesen. Schicke mir bitte die ID direkt.",
            )
            return GET_UID_STATE

        user_id = int(message.forward_from.id)
    else:
        user_id = int(cast(str, message.text))

    if user_id in roles[BOARD_ROLE].chat_ids:
        message.reply_text('Der Nutzer ist bereits Administrator. Nichts zu tun.')
        return ConversationHandler.END
    if user_id in roles[WATCHER_ROLE].chat_ids:
        message.reply_text(
            'Der Nutzer ist bereits ein Zuschauer. Soll er zum Administrator hochgestuft werden?',
            reply_markup=InlineKeyboardMarkup.from_row(
                [
                    InlineKeyboardButton(
                        text='Ja', callback_data=PROMOTE_USER.format(True, user_id)
                    ),
                    InlineKeyboardButton(
                        text='Nein', callback_data=PROMOTE_USER.format(False, user_id)
                    ),
                ]
            ),
        )
        return SELECT_ROLE_STATE
    message.reply_text(
        (
            'Soll der Nutzer Zuschauer oder Administrator werden? Den Unterschied erklärt die '
            'Anleitung.'
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text='Zuschauer', callback_data=ADD_USER.format(WATCHER_ROLE, user_id)
                    ),
                    InlineKeyboardButton(
                        text='Admin', callback_data=ADD_USER.format(BOARD_ROLE, user_id)
                    ),
                ],
                [InlineKeyboardButton('Anleitung 🤖', url=USER_GUIDE)],
            ]
        ),
    )
    return SELECT_ROLE_STATE


def add_user_promote_user(update: Update, context: CallbackContext) -> int:
    """
    Promotes a user to admin, if selected.

    Args:
        update: The incoming Telegram update.
        context: The context as provided by the :class:`telegram.ext.Dispatcher`.

    Returns:
        The next state.

    """
    message = cast(Message, update.effective_message)
    match = cast(Match, context.match)
    promote = str2bool(match.group(1))
    user_id = int(match.group(2))

    cast(CallbackQuery, update.callback_query).answer()
    if promote:
        roles = cast(Roles, context.bot_data[BOT_DATA_KEY])
        roles[WATCHER_ROLE].kick_member(user_id)
        roles[BOARD_ROLE].add_member(user_id)
        message.edit_text('Der Nutzer ist nun Administrator!')
    else:
        message.edit_text('Okay. Nichts passiert.')
    return ConversationHandler.END


def add_user_add_user(update: Update, context: CallbackContext) -> int:
    """
    Adds a user to the selected role.

    Args:
        update: The incoming Telegram update.
        context: The context as provided by the :class:`telegram.ext.Dispatcher`.

    Returns:
        The next state.

    """
    message = cast(Message, update.effective_message)
    match = cast(Match, context.match)
    role_name = match.group(1)
    user_id = int(match.group(2))
    roles = cast(Roles, context.bot_data[BOT_DATA_KEY])

    cast(CallbackQuery, update.callback_query).answer()
    roles[role_name].add_member(user_id)
    message.edit_text('Alles klar, ist erledigt!')
    return ConversationHandler.END


def kick_user_start(update: Update, _: CallbackContext) -> str:
    """
    Initializes the kick user conversation and asks the user to go to inline mode to select a
    user.

    Args:
        update: The incoming Telegram update.
        _: The context as provided by the :class:`telegram.ext.Dispatcher`.

    Returns:
        The next state.

    """
    cast(Message, update.effective_message).reply_text(
        'Wer soll rausfliegen? Klicke den Knopf unten und wähle einen Nutzer aus.',
        reply_markup=InlineKeyboardMarkup.from_button(
            InlineKeyboardButton('Klick Mich 👆', switch_inline_query_current_chat='')
        ),
    )
    return GET_UID_STATE


def kick_user_select_user(update: Update, context: CallbackContext) -> str:
    """
    Shows the list of currently allowed users.

    Args:
        update: The incoming Telegram update.
        context: The context as provided by the :class:`telegram.ext.Dispatcher`.

    Returns:
        The next state.

    """
    roles = cast(Roles, context.bot_data[BOT_DATA_KEY])
    results = []
    current_user_id = cast(User, update.effective_user).id
    for description, chat_ids in [
        ('Administrator', roles[BOARD_ROLE].chat_ids),
        ('Zuschauer', roles[WATCHER_ROLE].chat_ids),
    ]:
        for chat_id in chat_ids:
            if chat_id == current_user_id:
                continue

            # For new we just don't worry about flood limits here ...
            name = chat2str(chat_id, context.bot)
            article = InlineQueryResultArticle(
                id=str(chat_id),
                title=name,
                input_message_content=InputTextMessageContent(name),
                description=f'({description})',
            )

            results.append(article)

    cast(InlineQuery, update.inline_query).answer(
        results, auto_pagination=True, cache_time=0  # type: ignore[arg-type]
    )
    return KICK_USER_STATE


def kick_user_kick_user(update: Update, context: CallbackContext) -> int:
    """
    Kicks the selected user and confirms the action.

    Args:
        update: The incoming Telegram update.
        context: The context as provided by the :class:`telegram.ext.Dispatcher`.

    Returns:
        The next state.

    """
    roles = cast(Roles, context.bot_data[BOT_DATA_KEY])
    for role_name in (WATCHER_ROLE, BOARD_ROLE):
        role = roles[role_name]
        role.kick_member(int(cast(ChosenInlineResult, update.chosen_inline_result).result_id))
    cast(User, update.effective_user).send_message('Der Nutzer wurde entfernt.')
    return ConversationHandler.END


def build_add_user_conversation_handler(board_role: Role) -> ConversationHandler:
    """
    Gives a conversation handler that allows to add a user. Will only be accessible to the bot
    board.

    Args:
        board_role: The :attr:`bot.constants.BOARD_ROLE` role.

    """
    return ConversationHandler(
        entry_points=[
            RolesHandler(CommandHandler('nutzer_hinzufuegen', add_user_start), roles=board_role)
        ],
        states={
            GET_UID_STATE: [
                MessageHandler(
                    Filters.forwarded | Filters.regex(r'^\s*\d+\s*$'), add_user_get_uid
                ),
            ],
            SELECT_ROLE_STATE: [
                CallbackQueryHandler(add_user_promote_user, pattern=PROMOTE_USER_PATTERN),
                CallbackQueryHandler(add_user_add_user, pattern=ADD_USER_PATTERN),
            ],
            ConversationHandler.TIMEOUT: [MessageHandler(Filters.all, timeout)],
        },
        conversation_timeout=30,
        fallbacks=[],
    )


def build_kick_user_conversation_handler(board_role: Role) -> ConversationHandler:
    """
    Gives a conversation handler that allows to kick a user. Will only be accessible to the bot
    board.

    Args:
        board_role: The :attr:`bot.constants.BOARD_ROLE` role.

    """
    return ConversationHandler(
        entry_points=[
            RolesHandler(CommandHandler('nutzer_entfernen', kick_user_start), roles=board_role)
        ],
        states={
            GET_UID_STATE: [InlineQueryHandler(kick_user_select_user)],
            KICK_USER_STATE: [ChosenInlineResultHandler(kick_user_kick_user)],
            ConversationHandler.TIMEOUT: [TypeHandler(Update, timeout)],
        },
        conversation_timeout=30,
        fallbacks=[],
        per_chat=False,
    )
