import base64


class TelegramBot:

    def __init__(self, _telegram, botid):
        self.telegram = _telegram
        self.id = botid
        self.token = base64.urlsafe_b64encode(str(botid).encode()).decode().rstrip('=')
        self.conf = {
            'id': botid,
            'is_bot': True,
            'first_name': f'test{botid}',
            'username': f'test{botid}bot',
            'can_join_groups': True,
            'can_read_all_group_message': False,
            'supports_inline_queries': False,
        }

    def api_getme(self):
        return self.conf


class Telegram:

    def __init__(self):
        self.bots = {}

    def create_bot(self, botid):
        self.bots[botid] = bot = TelegramBot(self, botid)
        return bot
