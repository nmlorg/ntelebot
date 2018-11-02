"""A simple implementation of https://core.telegram.org/bots/api."""

from __future__ import absolute_import, division, print_function, unicode_literals

# pylint: disable=cyclic-import
from ntelebot import bot
from ntelebot import delayqueue
from ntelebot import dispatch
from ntelebot import errors
from ntelebot import keyboardutil
from ntelebot import loop
from ntelebot import preprocess
