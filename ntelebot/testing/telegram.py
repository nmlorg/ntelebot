import base64


class _User:

    def __init__(self, telegram, userid):
        self._telegram = telegram
        self.id = userid
        self.about = {
            'id': userid,
            'first_name': 'User',
            'last_name': str(userid),
            'username': f'user{userid}',
        }


class _Bot:

    def __init__(self, telegram, userid):
        self._telegram = telegram
        self.id = userid
        self.token = base64.urlsafe_b64encode(str(userid).encode()).decode().rstrip('=')
        self.about = {
            'id': userid,
            'is_bot': True,
            'first_name': f'Test Bot {userid}',
            'username': f'test{userid}bot',
        }
        self.conf = {
            'can_join_groups': True,
            'can_read_all_group_message': False,
            'supports_inline_queries': False,
        }


class _Chat:

    def __init__(self, telegram):
        self._telegram = telegram
        self.lastid = 77000
        self.messages = {}

    def send_message(self, sender, text):
        self.lastid += 1
        self._telegram.lastdate += 10
        msg = {
            'message_id': self.lastid,
            'from': sender,
            'date': self._telegram.lastdate,
            'text': text,
        }
        self.messages[msg['message_id']] = msg
        return msg


class _ChatView:

    def __init__(self, chat, sender, about):
        self.chat = chat
        self.sender = sender
        self.about = {'type': 'private'}
        self.about.update(about)

    def get_message(self, messageid):
        msg = self.chat.messages[messageid].copy()
        msg['from'] = msg['from'].about
        msg['chat'] = self.about
        return msg

    def send_message(self, text):
        msg = self.chat.send_message(self.sender, text)
        return self.get_message(msg['message_id'])


class Telegram:

    def __init__(self):
        self.lastdate = 66000000
        self.users = {}
        self.chats = {}

    def create_bot(self, userid):
        assert userid > 0 and userid not in self.users
        self.users[userid] = bot = _Bot(self, userid)
        return bot

    def create_private_chat(self, userid1, userid2):
        assert userid1 in self.users
        assert userid2 in self.users
        key = tuple(sorted((userid1, userid2)))
        assert key not in self.chats
        self.chats[key] = chat = _Chat(self)
        return chat

    def create_user(self, userid):
        assert userid > 0 and userid not in self.users
        self.users[userid] = user = _User(self, userid)
        return user

    def get_chat_view(self, sender, chatid):
        if chatid < 0:
            chat = self.chats.get(chatid)
            if not chat:
                raise self.ChatNotFound()
            return _ChatView(chat, sender, chat.about)

        otheruser = self.users.get(chatid)
        if not otheruser:
            raise self.ChatNotFound()
        key = tuple(sorted((sender.id, chatid)))
        chat = self.chats.get(key)
        if not chat:
            raise self.CanNotSend()
        return _ChatView(chat, sender, otheruser.about)

    class CanNotSend(Exception):
        pass

    class ChatNotFound(Exception):
        pass
