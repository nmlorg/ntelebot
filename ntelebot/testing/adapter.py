import json
import re

import requests

import ntelebot.testing.telegram


class NoMockAddress(Exception):

    def __init__(self, request):
        super().__init__(request)
        self.request = request

    def __str__(self):
        return f'{super().__str__()}: {self.request.url}'


class Adapter(requests.adapters.BaseAdapter):

    def __init__(self, telegram, botapi):
        super().__init__()
        self._telegram = telegram
        self._botapi = botapi

    def send(self, request, **unused_kwargs):
        match = re.match('https://api.telegram.org/bot([0-9]+):([a-zA-Z0-9-]+)/([a-z]+)$',
                         request.url)
        if not match:
            raise NoMockAddress(request)
        botid, token, method = match.groups()
        botid = int(botid)

        ctype = request.headers.get('content-type')
        if ctype == 'application/json':
            params = json.loads(request.body)
        else:
            params = {}

        resp = requests.Response()
        resp.request = request
        resp.headers['content-type'] = 'application/json'

        resp.status_code, data = self._handle(botid, token, method, params)

        if resp.status_code == 200:
            data = {'ok': True, 'result': data}
        else:
            data = {'ok': False, 'error_code': resp.status_code, 'description': data}
        resp._content = json.dumps(data).encode()

        return resp

    def _handle(self, botid, token, method, params):
        bot = self._telegram.users.get(botid)
        if not isinstance(bot, ntelebot.testing.telegram._Bot) or bot.token != token:
            return 401, 'Unauthorized'

        method = getattr(self._botapi, 'api_' + method, None)
        if not method:
            return 404, 'Not Found'

        return 200, method(bot, **params)

    def close(self):
        pass
