"""Tests for ntelebot.preprocess."""

from __future__ import absolute_import, division, print_function, unicode_literals

import ntelebot


class MockBot(object):
    # pylint: disable=missing-docstring
    token = 'BOT:TOKEN'

    def __init__(self):
        self.messages = {}
        self.parse_modes = {}
        self.queries = {}
        self.unauthorized = set()

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

    def send_message(self, chat_id=None, text=None, reply_to_message_id=None, parse_mode=None):
        if chat_id in self.unauthorized:
            raise ntelebot.errors.Unauthorized()

        self.messages[chat_id, None] = text
        self.parse_modes[chat_id, None] = parse_mode
        return reply_to_message_id and 'REPLY' or 'SEND'


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
    text = 'test \u2022 message'
    message = {'message_id': 3000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx
    assert ctx.user is user
    assert ctx.chat is chat
    assert ctx.text is text

    response_text = 'response \u2022 message'

    # Messages sent to group chats that do not trigger a forced-private response are replied back to
    # the group chat as a reply.
    assert ctx.reply_text(response_text) == 'REPLY'
    assert bot.messages[chat['id'], None] is response_text

    # However, messages sent to group chats whose responses are marked as private are sent back to
    # the user.
    bot.messages.clear()
    ctx.private = True
    assert ctx.reply_text(response_text) == 'SEND'
    assert bot.messages[user['id'], None] is response_text

    # However however, if a user sends a message to a group chat, and that user does not have a
    # private chat open with the bot, but the response is marked as private, the bot will try to
    # send the response in private but will fail, and end up sending a generic reply back to the
    # group chat.
    bot.messages.clear()
    bot.unauthorized.add(user['id'])
    assert ctx.reply_text(response_text) == 'REPLY'
    assert bot.messages[chat['id'], None] == (
        '<a href="https://t.me/user&quot;name?start=%s">Let\'s take this to a private chat!</a>' %
        ntelebot.preprocess.encode(text))
    assert bot.parse_modes[chat['id'], None] == 'HTML'


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
    assert ctx.text is text

    text = '/start /command'
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.text == '/command'

    text = '/start L2NvbW1hbmQ'  # base64.b64encode('/command')
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.text == '/command'

    text = 'L2NvbW1hbmQ'  # base64.b64encode('/command')
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.text == '/command'


def test_message_command():
    """Verify Context extracts command strings."""

    bot = MockBot()
    preprocessor = ntelebot.preprocess.Preprocessor()

    user = {'id': 1000}
    chat = {'id': 1000, 'type': 'private'}
    text = '/COMMAND'
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.text is text
    assert ctx.command == 'command'

    text = '/command arg'
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command == 'command'

    text = '/command@USER"NAME'
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command == 'command'

    text = '/command@otherbot'
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command is None

    text = 'test message'
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.command is None


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
    assert ctx.text == '/command \u2022 data test \u2022 message'

    # If the user did something to set a conversation, then sends a non-command message, then sends
    # a second non-command message, the conversation is not prepended.
    ctx = preprocessor(bot, {'message': message})
    assert ctx.text is text

    # Similarly, if the user did something to set a conversation, then sends a command message, the
    # bot discards the conversation.
    ctx.set_conversation('/command \u2022 data')
    text = '/new \u2022 command'
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.text is text

    # ... even if the second command doesn't set a conversation and the user sends a non-command
    # message (the previous conversation is not resumed).
    text = 'test \u2022 message'
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    ctx = preprocessor(bot, {'message': message})
    assert ctx.text is text


def test_encode():
    """Verify the deeplink encoder handles different types of strings reaonably."""

    assert ntelebot.preprocess.encode(b'') == b''
    assert ntelebot.preprocess.encode(u'') == b''
    assert ntelebot.preprocess.encode(b'test') == b'dGVzdA'
    assert ntelebot.preprocess.encode(u'test') == b'dGVzdA'
    assert ntelebot.preprocess.encode(u'\u2022') == b'4oCi'


def test_decode():
    """Verify the deeplink decoder handles different types of strings reaonably."""

    assert ntelebot.preprocess.decode(b'') == u''
    assert ntelebot.preprocess.decode(u'') == u''
    assert ntelebot.preprocess.decode(b'dGVzdA') == u'test'
    assert ntelebot.preprocess.decode(u'dGVzdA') == u'test'
    assert ntelebot.preprocess.decode(u'4oCi') == u'\u2022'
    assert ntelebot.preprocess.decode(u'\u2022') == u''

    # Gibberish, triggering TypeError in Python 2.7 and binascii.Error (which derives from
    # ValueError) in Python 3.6 for incorrect padding.
    assert ntelebot.preprocess.decode(b'a') == u''

    # b'\xff', triggering UnicodeDecodeError.
    assert ntelebot.preprocess.decode(b'/w') == u''