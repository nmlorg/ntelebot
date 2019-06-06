"""A simple implementation of https://core.telegram.org/bots/api."""

import requests

import ntelebot


class Bot(object):  # pylint: disable=too-few-public-methods
    """A simple implementation of https://core.telegram.org/bots/api."""

    BASE_URL = 'https://api.telegram.org/bot'

    def __init__(self, token, timeout=12):
        assert token.count(':') == 1 and token.split(':')[0].isdigit() and '/' not in token, token
        self.token = token
        self.url = '%s%s/' % (self.BASE_URL, token)
        self.timeout = timeout

    def __getattr__(self, k):
        api_key = k.lower().replace('_', '')
        if api_key == k:
            request = _Request(self.url + api_key, self.timeout)
        else:
            request = getattr(self, api_key)
        setattr(self, k, request)
        return request

    _username = None

    @property
    def username(self):  # pylint: disable=missing-docstring
        if self._username is None:
            self._username = self.get_me()['username']
        return self._username

    def encode_link(self, command, text=None):
        """Generate an HTML fragment that links to a deeplink back to the bot."""

        return ntelebot.deeplink.encode_link(self.username, command, text=text)

    def encode_url(self, command):
        """Generate a deeplink URL."""

        return ntelebot.deeplink.encode_url(self.username, command)


class _Request(object):  # pylint: disable=too-few-public-methods

    def __init__(self, url, timeout):
        self.url = url
        self.timeout = timeout

    def __call__(self, **params):
        try:
            data = requests.post(self.url, timeout=self.timeout, json=params).json()
        except requests.exceptions.ReadTimeout as exc:
            raise ntelebot.errors.Timeout(exc)
        if data['ok']:
            return data['result']
        if data['error_code'] == 401:
            raise ntelebot.errors.Unauthorized(data)
        if data['error_code'] == 403:
            raise ntelebot.errors.Forbidden(data)
        if data['error_code'] == 404:
            raise ntelebot.errors.NotFound(data)
        if data['error_code'] == 409:
            raise ntelebot.errors.Conflict(data)
        raise ntelebot.errors.Error(data)
