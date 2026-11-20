"""Tests for ntelebot.preprocess."""

import ntelebot


class MockBot(ntelebot.bot.Bot):
    # pylint: disable=missing-docstring

    def __init__(self):
        super().__init__('1234:TOKEN')
        self.unauthorized = set()
        self._log = []

    def __getattr__(self, method):

        def func(**kwargs):
            if 'chat_id' in kwargs and kwargs['chat_id'] in self.unauthorized:
                raise ntelebot.errors.Forbidden()
            self._log.append(
                f"{method}({', '.join(f'{k}={repr(v)}' for k, v in sorted(kwargs.items()))})")
            return {'message_id': kwargs.get('message_id', 9999)}

        setattr(self, method, func)
        return func

    @staticmethod
    def get_me():
        return {'username': 'user"name'}

    @property
    def log(self):
        log = self._log
        self._log = []
        return '\n'.join(log)


def test_unknown_update():
    """Verify updates that the preprocessor doesn't understand are handled gracefully."""

    bot = MockBot()
    preprocessor = ntelebot.preprocess.Preprocessor()
    assert preprocessor(bot, {}) is None


def test_callback_query():
    """Verify Preprocessor and Context handle CallbackQuery updates correctly."""

    bot = MockBot()
    preprocessor = ntelebot.preprocess.Preprocessor()

    user = {'id': 1000}
    chat = {'id': 2000}
    message = {'message_id': 3000, 'chat': chat}
    text = 'test \u2022 message'
    callback_query = {'id': 4000, 'from': user, 'message': message, 'data': text}
    ctx = preprocessor(bot, {'callback_query': callback_query})
    assert ctx
    assert ctx.user is user
    assert ctx.chat is chat
    assert ctx.text is text

    response_text = 'response \u2022 message'
    ctx.reply_text(response_text)
    assert bot.log == "edit_message_text(chat_id=2000, message_id=3000, text='response • message')"


def test_inline_query():
    """Verify Preprocessor and Context handle InlineQuery updates correctly."""

    bot = MockBot()
    preprocessor = ntelebot.preprocess.Preprocessor()

    user = {'id': 1000}
    text = 'test \u2022 message'
    inline_query = {'id': 2000, 'from': user, 'query': text}
    ctx = preprocessor(bot, {'inline_query': inline_query})
    assert ctx
    assert ctx.user is user
    assert ctx.chat is None
    assert ctx.text is text

    response_list = ['response \u2022 message']
    ctx.reply_inline(response_list)
    assert bot.log == "answer_inline_query(inline_query_id=2000, results=['response • message'])"


def test_message_private():
    """Verify Preprocessor and Context handle private Message updates correctly."""

    bot = MockBot()
    preprocessor = ntelebot.preprocess.Preprocessor()

    user = {'id': 1000}
    chat = {'id': 2000, 'type': 'private'}  # Note in reality chat.id == user.id.
    text = 'test \u2022 message'
    message = {'message_id': 3000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx
    assert ctx.user is user
    assert ctx.chat is chat
    assert ctx.text is text

    response_text = 'response \u2022 message'

    # Messages sent in private chats are always replied back to the private chat as a new message.
    ctx.reply_text(response_text)
    assert bot.log == "send_message(chat_id=1000, text='response • message')"

    # ... even when the command is marked as private.
    ctx.private = True
    ctx.reply_text(response_text)
    assert bot.log == "send_message(chat_id=1000, text='response • message')"


def test_message_group():
    """Verify Preprocessor and Context handle group chat Message updates correctly."""

    bot = MockBot()
    preprocessor = ntelebot.preprocess.Preprocessor()

    user = {'id': 1000}
    chat = {'id': 2000, 'type': 'supergroup'}
    text = '/test@user"name \u2022 message'
    message = {'message_id': 3000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx
    assert ctx.user is user
    assert ctx.chat is chat
    assert ctx.command == 'test'
    assert ctx.text == '\u2022 message'

    response_text = 'response \u2022 message'

    # pylint: disable=line-too-long

    # Messages sent to group chats that do not trigger a forced-private response are replied back to
    # the group chat as a reply.
    ctx.reply_text(response_text)
    assert bot.log == "send_message(chat_id=2000, reply_parameters={'message_id': 3000, 'chat_id': 2000, 'allow_sending_without_reply': True}, text='response • message')"

    # However, messages sent to group chats whose responses are marked as private are sent back to
    # the user.
    ctx.private = True
    ctx.reply_text(response_text)
    assert bot.log == """\
send_message(chat_id=1000, reply_parameters={'message_id': 3000, 'chat_id': 2000, 'allow_sending_without_reply': True}, text='response • message')
send_message(chat_id=2000, reply_parameters={'message_id': 3000, 'chat_id': 2000, 'allow_sending_without_reply': True}, text='(I replied in private.)')"""

    # However however, if a user sends a message to a group chat, and that user does not have a
    # private chat open with the bot, but the response is marked as private, the bot will try to
    # send the response in private but will fail, and end up sending a generic reply back to the
    # group chat.
    bot.unauthorized.add(user['id'])
    ctx.reply_text(response_text)
    assert bot.log == """\
send_message(chat_id=2000, reply_markup={'inline_keyboard': [[{'text': "Resend '/test • message' in private", 'url': 'https://t.me/user"name?start=L3Rlc3Qg4oCiIG1lc3NhZ2U'}]]}, reply_parameters={'message_id': 3000, 'chat_id': 2000, 'allow_sending_without_reply': True}, text="That's too noisy to answer here. I tried to reply in private, but I can only send you a message if you already have a private chat open with me… and it looks like you don't 😞\\n\\nClick my name/picture, then the 💬 icon, then retype your command there; or click the button below and your Telegram app will do all that automatically.\\n\\n(I'll delete this in a minute.)")"""


def test_channel_post():
    """Verify Preprocessor and Context handle channel_post updates correctly."""

    bot = MockBot()
    preprocessor = ntelebot.preprocess.Preprocessor()

    chat = {'id': 2000, 'type': 'channel'}
    text = '/test@user"name \u2022 message'
    channel_post = {'message_id': 3000, 'chat': chat, 'author_signature': 'User Name', 'text': text}
    ctx = preprocessor(bot, {'channel_post': channel_post})
    assert ctx
    assert ctx.type == 'message'
    assert ctx.user is None
    assert ctx.chat is chat
    assert ctx.command == 'test'
    assert ctx.text == '\u2022 message'


def test_message_reply_variations():
    """Verify Context's reply_* methods."""

    bot = MockBot()
    preprocessor = ntelebot.preprocess.Preprocessor()

    user = {'id': 1000}
    chat = {'id': 1000, 'type': 'private'}
    text = 'test \u2022 message'
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    response_text = 'format \u2022 %s'
    ctx.reply_text(response_text, 'arg \u2022')
    assert bot.log == "send_message(chat_id=1000, text='format • arg •')"

    ctx.reply_html(response_text)
    assert bot.log == "send_message(chat_id=1000, parse_mode='HTML', text='format • %s')"

    ctx.reply_markdown(response_text)
    assert bot.log == "send_message(chat_id=1000, parse_mode='Markdown', text='format • %s')"


def test_message_slash_start():
    """Verify Preprocessor handles the /start command (used by deeplinks) correctly."""

    bot = MockBot()
    preprocessor = ntelebot.preprocess.Preprocessor()

    user = {'id': 1000}
    chat = {'id': 1000, 'type': 'private'}
    text = '/start'
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command == 'start'
    assert ctx.text == ''

    text = '/start /command'
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command == 'command'
    assert ctx.text == ''

    text = '/start L2NvbW1hbmQ'  # base64.b64encode('/command')
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command == 'command'
    assert ctx.text == ''

    text = 'L2NvbW1hbmQ'  # base64.b64encode('/command')
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command == 'command'
    assert ctx.text == ''


def test_message_command():
    """Verify Context extracts command strings."""

    bot = MockBot()
    preprocessor = ntelebot.preprocess.Preprocessor()

    user = {'id': 1000}
    chat = {'id': 1000, 'type': 'private'}
    text = '/COMMAND'
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command == 'command'
    assert ctx.text == ''

    text = '/command   arg1   arg2   arg3'
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command == 'command'
    assert ctx.text == 'arg1   arg2   arg3'
    assert ctx.split(2) == ['arg1', 'arg2   arg3']
    assert ctx.split(3) == ['arg1', 'arg2', 'arg3']
    assert ctx.split(4) == ['arg1', 'arg2', 'arg3', '']

    text = '/command@USER"NAME'
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command == 'command'
    assert ctx.text == ''

    text = '/command@otherbot'
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command is None
    assert ctx.text is text

    text = 'test message'
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command is None
    assert ctx.text is text


def test_message_conversations():
    """Verify Preprocessor and Context handle manually configured conversations correctly."""

    bot = MockBot()
    preprocessor = ntelebot.preprocess.Preprocessor()

    user = {'id': 1000}
    chat = {'id': 1000, 'type': 'private'}
    text = 'test \u2022 message'
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.text is text

    # If a user does something that causes the bot to set its conversation, then sends a non-command
    # message, the bot acts as if the user sent the previous conversation text prepended to their
    # actual message.
    ctx.set_conversation('/command \u2022 data')
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command == 'command'
    assert ctx.text == '\u2022 data test \u2022 message'

    ctx.set_conversation('no \u2022 command')
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command == 'command'
    assert ctx.text == 'no \u2022 command test \u2022 message'

    # If the user did something to set a conversation, then sends a non-command message, then sends
    # a second non-command message, the conversation is not prepended.
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command is None
    assert ctx.text is text

    # Similarly, if the user did something to set a conversation, then sends a command message, the
    # bot discards the conversation.
    ctx.set_conversation('/command \u2022 data')
    text = '/new \u2022 command'
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command == 'new'
    assert ctx.text == '\u2022 command'

    # ... even if the second command doesn't set a conversation and the user sends a non-command
    # message (the previous conversation is not resumed).
    text = 'test \u2022 message'
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command is None
    assert ctx.text is text


def test_forward_from():
    """Verify Preprocessor handles forwarded messages correctly."""

    bot = MockBot()
    preprocessor = ntelebot.preprocess.Preprocessor()

    user = {'id': 1000}
    chat = {'id': 1000, 'type': 'private'}
    text = '/acommand arg'
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command == 'acommand'
    assert ctx.text == 'arg'
    assert not ctx.forwarded
    assert ctx.forward_from is None
    ctx.set_conversation('arg')

    message['text'] = '/ignored'
    message['forward_date'] = 1000
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command == 'acommand'
    assert ctx.text == 'arg'
    assert ctx.forwarded
    assert ctx.forward_from is None
    ctx.set_conversation('arg')

    other = {'id': 5000}
    message['forward_from'] = other
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command == 'acommand'
    assert ctx.text == 'arg'
    assert ctx.forwarded
    assert ctx.forward_from == 5000


def test_reply_to_message():
    """Verify Preprocessor handles replies correctly."""

    bot = MockBot()
    preprocessor = ntelebot.preprocess.Preprocessor()

    user = {'id': 1000}
    chat = {'id': 1000, 'type': 'private'}
    text = '/acommand arg'
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command == 'acommand'
    assert ctx.text == 'arg'
    assert ctx.reply_from is None
    ctx.set_conversation('arg')

    text = '/reply command'
    otheruser = {'id': 5000}
    othertext = '/ignored'
    othermessage = {'message_id': 3000, 'chat': chat, 'from': otheruser, 'text': othertext}
    message = {
        'message_id': 2000,
        'chat': chat,
        'from': user,
        'text': text,
        'reply_to_message': othermessage,
    }
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command == 'reply'
    assert ctx.text == 'command'
    assert ctx.reply_from == 5000


def test_media():
    """Verify Preprocessor handles media attachments correctly."""

    bot = MockBot()
    preprocessor = ntelebot.preprocess.Preprocessor()

    user = {'id': 1000}
    chat = {'id': 1000, 'type': 'private'}
    anim = {
        'duration': 2,
        'file_id': 'DDD2345',
        'file_name': 'DDD2345.mp4',
        'file_size': 450000,
        'height': 400,
        'mime_type': 'video/mp4',
        'thumb': {
            'file_id': 'DDD3456',
            'file_size': 4000,
            'height': 90,
            'width': 90,
        },
        'width': 400,
    }
    doc = {
        'file_id': 'DDD2345',
        'file_name': 'DDD2345.mp4',
        'file_size': 450000,
        'mime_type': 'video/mp4',
        'thumb': {
            'file_id': 'DDD3456',
            'file_size': 4000,
            'height': 90,
            'width': 90,
        },
    }
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'animation': anim, 'document': doc}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.document == 'DDD2345'
    assert ctx.photo is None
    assert ctx.sticker is None

    photos = [
        {
            'file_id': '76543',
            'file_size': 1000,
            'height': 67,
            'width': 90,
        },
        {
            'file_id': '98765',
            'file_size': 30000,
            'height': 480,
            'width': 640,
        },
        {
            'file_id': '87654',
            'file_size': 15000,
            'height': 240,
            'width': 320,
        },
    ]
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'photo': photos}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.document is None
    assert ctx.photo == '98765'
    assert ctx.sticker is None

    sticker = {
        'emoji': ' ',
        'file_id': 'AAA1234',
        'file_size': 10000,
        'height': 512,
        'set_name': 'Sticker Set Name',
        'thumb': {
            'file_id': 'BBB1234',
            'file_size': 5000,
            'height': 128,
            'width': 128,
        },
        'width': 512,
    }
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'sticker': sticker}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.document is None
    assert ctx.photo is None
    assert ctx.sticker == 'AAA1234'

    ctx.reply_text('document:DOCUMENT_ID MY TEXT')
    assert bot.log == "send_document(caption='MY TEXT', chat_id=1000, document='DOCUMENT_ID')"
    ctx.reply_text('document:DOCUMENT_ID')
    assert bot.log == "send_document(chat_id=1000, document='DOCUMENT_ID')"
    ctx.reply_text('photo:PHOTO_ID MY TEXT')
    assert bot.log == "send_photo(caption='MY TEXT', chat_id=1000, photo='PHOTO_ID')"
    ctx.reply_text('photo:PHOTO_ID')
    assert bot.log == "send_photo(chat_id=1000, photo='PHOTO_ID')"
    ctx.reply_text('sticker:BOGUS DATA')
    assert bot.log == "send_message(chat_id=1000, text='sticker:BOGUS DATA')"
    ctx.reply_text('sticker:STICKER_ID')
    assert bot.log == "send_sticker(chat_id=1000, sticker='STICKER_ID')"


def test_new_chat_members():
    """Verify Preprocessor handles new_chat_members messages correctly."""

    bot = MockBot()
    preprocessor = ntelebot.preprocess.Preprocessor()

    user = {'id': 1000}
    chat = {'id': 1000, 'type': 'private'}
    other = {'id': 5000}
    text = '/ignored'
    message = {
        'message_id': 2000,
        'chat': chat,
        'from': user,
        'text': text,
        'new_chat_members': [other],
    }
    ctx = preprocessor(bot, {'message': message})
    assert ctx.type == 'join'
    assert ctx.command is None
    assert ctx.text is None
    assert ctx.data == [other]


def test_pinned_message():
    """Verify Preprocessor handles pinned_message messages correctly."""

    bot = MockBot()
    preprocessor = ntelebot.preprocess.Preprocessor()

    chat = {'id': 1000, 'type': 'private'}
    pinned_user = {'id': 5000}
    pinned_text = 'pinned text'
    pinned_message = {'message_id': 6000, 'chat': chat, 'from': pinned_user, 'text': pinned_text}
    user = {'id': 1000}
    text = '/ignored'
    message = {
        'message_id': 2000,
        'chat': chat,
        'from': user,
        'text': text,
        'pinned_message': pinned_message,
    }
    ctx = preprocessor(bot, {'message': message})
    assert ctx.type == 'pin'
    assert ctx.command is None
    assert ctx.text is None
    assert ctx.data == pinned_message
