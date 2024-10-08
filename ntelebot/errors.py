"""All exceptions used by ntelebot."""


class Error(Exception):
    """Base ntelebot error."""

    description = error_code = None

    def __init__(self, data=None):
        super().__init__(data)
        if isinstance(data, dict):
            self.__dict__.update(data)


class Conflict(Error):
    """HTTP 409 Conflict."""


class Forbidden(Error):
    """HTTP 403 Forbidden."""


class NotFound(Error):
    """HTTP 404 Not Found."""


class Timeout(Error):
    """Telegram didn't respond within the bot's request timeout."""


class TooLong(Error):
    """HTTP 400, Telegram MESSAGE_TOO_LONG."""


class Unauthorized(Error):
    """HTTP 401 Unauthorized."""


class Unmodified(Error):
    """HTTP 400, Telegram MESSAGE_NOT_MODIFIED."""
