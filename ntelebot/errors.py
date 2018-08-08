"""All exceptions used by ntelebot."""

from __future__ import absolute_import, division, print_function, unicode_literals


class Error(Exception):
    """Base ntelebot error."""


class NotFound(Error):
    """HTTP 404 Not Found."""


class Timeout(Error):
    """Telegram didn't respond within the bot's request timeout."""


class Unauthorized(Error):
    """HTTP 401 Unauthorized."""
