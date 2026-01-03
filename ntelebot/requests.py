"""A wrapper around requests.api.* that reuses a single Session instance per thread."""

import socket
import threading

import requests
from requests.exceptions import *  # pylint: disable=redefined-builtin,unused-wildcard-import,wildcard-import
import urllib3


class _Local(threading.local):  # pylint: disable=too-few-public-methods

    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        adapter = _KeepAliveAdapter()
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)


class _KeepAliveAdapter(requests.adapters.HTTPAdapter):

    def init_poolmanager(self, *args, **kwargs):
        assert 'socket_options' not in kwargs
        # See https://github.com/nmlorg/ntelebot/issues/9#issuecomment-2302631974.
        kwargs['socket_options'] = urllib3.connection.HTTPConnection.default_socket_options + [
            (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
            (socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 115),
            (socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 30),
            (socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 4),
        ]
        return super().init_poolmanager(*args, **kwargs)


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
