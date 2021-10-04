"""A simple implementation of https://core.telegram.org/bots/api."""

import io
import json

import requests

import ntelebot


class Bot(object):  # pylint: disable=too-few-public-methods
    """A simple implementation of https://core.telegram.org/bots/api."""

    BASE_URL = 'https://api.telegram.org/bot'

    def __init__(self, token, timeout=12):
        assert token.count(':') == 1 and token.split(':')[0].isdigit() and '/' not in token, token
        self.token = token
        self.url = f'{self.BASE_URL}{token}/'
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
            data = requests.post(self.url, timeout=self.timeout, **_prepare(params)).json()
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


def _prepare(params):
    files = {}
    data = _separate_files(files, params)

    if not files:
        return {'json': data}

    # See https://github.com/nmlorg/ntelebot/issues/7#issuecomment-933581503.
    for key, value in data.items():
        if not isinstance(value, str):
            data[key] = json.dumps(value)
    return {'data': data, 'files': files}


def _separate_files(files, params):
    if isinstance(params, dict):
        return {k: _separate_files(files, v) for k, v in params.items()}
    if isinstance(params, (list, tuple)):
        return [_separate_files(files, v) for v in params]
    if isinstance(params, io.IOBase):
        attachid = f'file{len(files)}'
        files[attachid] = ('', params.read())
        return f'attach://{attachid}'
    return params
