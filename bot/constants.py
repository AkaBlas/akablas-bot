#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The module contains constants used throughout the bot."""
from typing import List
import pytz

INSTRUMENTS: List['str'] = [
    'Flöten & Oboen',
    'Klarinetten',
    'Altsaxsophone',
    'Tenorsaxophone, Baritonsaxophone',
    'Trompeten',
    'Flügelhörner',
    'Tenorhörner, Hörner, Baritone, Fagotte',
    'Posaunen',
    'Tuben, Gitarren, Bässe',
]
"""
List[:obj:`str`]: List of instrument groups in the order that they be assigned to swipe the
rehearsal room.
"""


HOMEPAGE: str = 'https://hirschheissich.gitlab.io/akablas-bot/'
""":obj:`str`: Homepage of this bot."""
USER_GUIDE: str = f'{HOMEPAGE}userguide.html'
""":obj:`str`: User guide for this bot."""
TIMEZONE: pytz.BaseTzInfo = pytz.timezone('Europe/Berlin')
""":class:`pytz.BaseTzInfo`: Timezone object for Europe/Berlin"""


# Keys
LAST_SWEEP_KEY = 'offset'
"""
:obj:`str`: Key for the ``bot_data``. The corresponding value is expected to be a tuple of
    :obj:`datetime.date` and :obj:`int`, where the latter is an index of :attr:`INSTRUMENTS`
    stating which instrument groups turn to swipe it was at the specified date of the last
    rehearsal.
"""
PAUSED_WEEKS_KEY = 'paused_weeks'
"""
:obj:`str`: Key for the ``bot_data``. The corresponding value is expected to be a set of
    :obj:`datetime.date` objects specifying tuesdays without rehearsal.
"""
PAUSED_KEY = 'paused'
"""
:obj:`str`: Key for the ``bot_data``. The corresponding value is expected to be a
    :obj:`datetime.date` indicating the start of the pause, if rehearsals are paused, or
    :obj:`False`.
"""
BOARD_ROLE = 'board_role'
"""
:obj:`str`: Name of the :class:`ptbcontrib.roles.Role` for the board.
"""
WATCHER_ROLE = 'watcher_role'
"""
:obj:`str`: Name of the :class:`ptbcontrib.roles.Role` for the watchers, i.e. chats that can see
    who's turn it is for swiping but can't administrate the bot.
"""

# Callback Data
PROMOTE_USER: str = 'promote_user {} {}'
"""
:obj:`str`: Callback data to promote a user. Use as ``PROMOTE_USER.format(promote_bool, user_id)``.
"""
PROMOTE_USER_PATTERN: str = r'^promote_user (True|False) (\d+)$'
"""
:obj:`str`: Callback data to catch :attr:`PROMOTE_USER`. The boolean and user id will be available
    as matches.
"""
ADD_USER: str = 'add_user {} {}'
"""
:obj:`str`: Callback data to add a user. Use as ``ADD_USER.format(role_name, user_id)``.
"""
ADD_USER_PATTERN: str = rf'^add_user ({BOARD_ROLE}|{WATCHER_ROLE}) (\d+)$'
"""
:obj:`str`: Callback data to catch :attr:`ADD_USER`. The selected role and user id will be
    available as matches.
"""
PAUSE_BUTTON: str = 'pause_button {} {}'
"""
:obj:`str`: Callback data to pause a week. Use as ``PAUSE_BUTTON.format(date.isoformat(), paused)``
"""
PAUSE_BUTTON_PATTERN: str = r'^pause_button (\d{4}-\d{2}-\d{2}) (True|False)$'
"""
:obj:`str`: Callback data to catch :attr:`PAUSE_BUTTON_PATTERN`. The selected tuesday and whether a
    rehearsal should take place or not will be available as matches.
"""
PAUSE_NAVIGATION_BUTTON: str = 'pause_nav_button {}'
"""
:obj:`str`: Callback data to navigate between weeks while pausing a weeks. Use as
    ``PAUSE_NAVIGATION_BUTTON.format(date.isoformat())``.
"""
PAUSE_NAVIGATION_BUTTON_PATTERN: str = r'^pause_nav_button (\d{4}-\d{2}-\d{2})$'
"""
:obj:`str`: Callback data to catch :attr:`PAUSE_NAVIGATION_BUTTON`. The selected tuesday will be
    available as match.
"""
PAUSE_NAVIGATION_DONE: str = 'pause_navigation_done'
"""
:obj:`str`: Callback data to finish pausing weeks.
"""
