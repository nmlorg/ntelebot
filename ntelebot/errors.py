"""All exceptions used by ntelebot."""


class Error(Exception):
    """Base ntelebot error."""

    description = error_code = None

    def __init__(self, data=None):
        super().__init__(data)
        if isinstance(data, dict):
            self.__dict__.update(data)


class BadGateway(Error):
    """HTTP 502 Bad Gateway."""


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


class TooManyRequests(Error):
    """HTTP 429 Too Many Requests."""

    retry_after = None

    def __init__(self, data=None):
        super().__init__(data)
        if data and (params := data.get('parameters')):
            self.retry_after = params.get('retry_after')


class Unauthorized(Error):
    """HTTP 401 Unauthorized."""


class Unmodified(Error):
    """HTTP 400, Telegram MESSAGE_NOT_MODIFIED."""
