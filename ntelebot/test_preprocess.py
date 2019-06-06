"""Tests for ntelebot.preprocess."""

import ntelebot


class MockBot(ntelebot.bot.Bot):
    # pylint: disable=missing-docstring

    def __init__(self):
        super(MockBot, self).__init__('1234:TOKEN')
        self.messages = {}
        self.parse_modes = {}
        self.queries = {}
        self.unauthorized = set()

    @staticmethod
    def __getattr__(k):  # pragma: no cover
        raise AttributeError(k)

    def answer_inline_query(self, inline_query_id=None, results=None):
        self.queries[inline_query_id] = results
        return 'ANSWER'

    def edit_message_text(self, chat_id=None, message_id=None, text=None, parse_mode=None):
        self.messages[chat_id, message_id] = text
        self.parse_modes[chat_id, message_id] = parse_mode
        return 'EDIT'

    @staticmethod
    def get_me():
        return {'username': 'user"name'}

    def send_message(  # pylint: disable=unused-argument,too-many-arguments
            self,
            chat_id=None,
            text=None,
            reply_to_message_id=None,
            disable_web_page_preview=None,
            parse_mode=None):
        if chat_id in self.unauthorized:
            raise ntelebot.errors.Forbidden()

        self.messages[chat_id, None] = text
        self.parse_modes[chat_id, None] = parse_mode
        return reply_to_message_id and 'REPLY' or 'SEND'

    @staticmethod
    def send_document(chat_id=None, document=None):  # pylint: disable=unused-argument
        return 'DOCUMENT'

    @staticmethod
    def send_photo(chat_id=None, photo=None):  # pylint: disable=unused-argument
        return 'PHOTO'

    @staticmethod
    def send_sticker(chat_id=None, sticker=None):  # pylint: disable=unused-argument
        return 'STICKER'


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
    assert ctx.reply_text(response_text) == 'EDIT'
    assert bot.messages[chat['id'], message['message_id']] is response_text


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
    assert ctx.reply_inline(response_list) == 'ANSWER'
    assert bot.queries[inline_query['id']] is response_list


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
    assert ctx.reply_text(response_text) == 'SEND'
    assert bot.messages[user['id'], None] is response_text

    # ... even when the command is marked as private.
    bot.messages.clear()
    ctx.private = True
    assert ctx.reply_text(response_text) == 'SEND'
    assert bot.messages[user['id'], None] is response_text


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

    # Messages sent to group chats that do not trigger a forced-private response are replied back to
    # the group chat as a reply.
    assert ctx.reply_text(response_text) == 'REPLY'
    assert bot.messages[chat['id'], None] is response_text
    bot.messages.clear()

    # However, messages sent to group chats whose responses are marked as private are sent back to
    # the user.
    ctx.private = True
    assert ctx.reply_text(response_text) == 'SEND'
    assert bot.messages[user['id'], None] is response_text
    bot.messages.clear()

    # However however, if a user sends a message to a group chat, and that user does not have a
    # private chat open with the bot, but the response is marked as private, the bot will try to
    # send the response in private but will fail, and end up sending a generic reply back to the
    # group chat.
    bot.unauthorized.add(user['id'])
    assert ctx.reply_text(response_text) == 'REPLY'
    assert bot.messages[chat['id'], None] == (
        '<a href="https://t.me/user&quot;name?start=L3Rlc3Qg4oCiIG1lc3NhZ2U">Let\'s take this to a '
        'private chat!</a>')
    assert bot.parse_modes[chat['id'], None] == 'HTML'
    bot.messages.clear()


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
    assert bot.messages[user['id'], None] == 'format \u2022 arg \u2022'
    assert bot.parse_modes[user['id'], None] is None

    bot.parse_modes.clear()
    ctx.reply_html(response_text)
    assert bot.parse_modes[user['id'], None] == 'HTML'

    bot.parse_modes.clear()
    ctx.reply_markdown(response_text)
    assert bot.parse_modes[user['id'], None] == 'Markdown'


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
    assert ctx.forward_from is None
    ctx.set_conversation('arg')

    text = '/ignored'
    other = {'id': 5000}
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text, 'forward_from': other}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command == 'acommand'
    assert ctx.text == 'arg'
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

    assert ctx.reply_text('document:BOGUS DATA') == 'SEND'
    assert ctx.reply_text('document:DOCUMENT_ID') == 'DOCUMENT'
    assert ctx.reply_text('photo:BOGUS DATA') == 'SEND'
    assert ctx.reply_text('photo:PHOTO_ID') == 'PHOTO'
    assert ctx.reply_text('sticker:BOGUS DATA') == 'SEND'
    assert ctx.reply_text('sticker:STICKER_ID') == 'STICKER'


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
