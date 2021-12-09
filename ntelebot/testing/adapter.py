import json
import re

import requests


class NoMockAddress(Exception):

    def __init__(self, request):
        super().__init__(request)
        self.request = request

    def __str__(self):
        return f'{super().__str__()}: {self.request.url}'


class Adapter(requests.adapters.BaseAdapter):

    def __init__(self, telegram):
        super().__init__()
        self.telegram = telegram

    def send(self, request, **unused_kwargs):
        match = re.match('https://api.telegram.org/bot([0-9]+):([a-zA-Z0-9-]+)/([a-z]+)$',
                         request.url)
        if not match:
            raise NoMockAddress(request)
        botid, token, method = match.groups()
        botid = int(botid)

        resp = requests.Response()
        resp.request = request
        resp.headers['content-type'] = 'application/json'

        resp.status_code, data = self._handle(botid, token, method)

        if resp.status_code == 200:
            data = {'ok': True, 'result': data}
        else:
            data = {'ok': False, 'error_code': resp.status_code, 'description': data}
        resp._content = json.dumps(data).encode()

        return resp

    def _handle(self, botid, token, method):
        bot = self.telegram.bots.get(botid)
        if not bot or bot.token != token:
            return 401, 'Unauthorized'

        method = getattr(bot, method, None)
        if not method:
            return 404, 'Not Found'

        return 200, method()

    def close(self):
        pass