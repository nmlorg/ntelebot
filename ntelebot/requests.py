"""A wrapper around requests.api.* that reuses a single Session instance per thread."""

import threading

import requests
from requests.exceptions import *  # pylint: disable=redefined-builtin,unused-wildcard-import,wildcard-import


class _Local(threading.local):  # pylint: disable=too-few-public-methods

    def __init__(self):
        super().__init__()
        self.session = requests.Session()


_LOCAL = _Local()

# pylint: disable=missing-function-docstring


def request(*args, **kwargs):
    return _LOCAL.session.request(*args, **kwargs)


def get(*args, **kwargs):
    return _LOCAL.session.get(*args, **kwargs)


def options(*args, **kwargs):
    return _LOCAL.session.options(*args, **kwargs)


def head(*args, **kwargs):
    return _LOCAL.session.head(*args, **kwargs)


def post(*args, **kwargs):
    return _LOCAL.session.post(*args, **kwargs)


def put(*args, **kwargs):
    return _LOCAL.session.put(*args, **kwargs)


def patch(*args, **kwargs):
    return _LOCAL.session.patch(*args, **kwargs)


def delete(*args, **kwargs):
    return _LOCAL.session.delete(*args, **kwargs)
