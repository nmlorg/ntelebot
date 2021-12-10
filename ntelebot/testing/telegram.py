import base64


class _Bot:

    def __init__(self, telegram, userid):
        self._telegram = telegram
        self.id = userid
        self.token = base64.urlsafe_b64encode(str(userid).encode()).decode().rstrip('=')
        self.conf = {
            'id': userid,
            'is_bot': True,
            'first_name': f'test{userid}',
            'username': f'test{userid}bot',
            'can_join_groups': True,
            'can_read_all_group_message': False,
            'supports_inline_queries': False,
        }


class Telegram:

    def __init__(self):
        self.users = {}

    def create_bot(self, userid):
        assert userid not in self.users
        self.users[userid] = bot = _Bot(self, userid)
        return bot
