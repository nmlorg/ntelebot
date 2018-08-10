"""Non-universal, but fairly versatile update preprocessor."""

from __future__ import absolute_import, division, print_function, unicode_literals

import base64
import cgi

import ntelebot


class Preprocessor(object):  # pylint: disable=too-few-public-methods
    """Non-universal, but fairly versatile update preprocessor."""

    def __init__(self):
        self.conversations = {}
        self.bots = {}

    def __call__(self, bot, update):
        """Convert a Telegram Update instance into a normalized Context."""

        bot_info = self.bots.get(bot.token)
        if not bot_info:
            self.bots[bot.token] = bot_info = bot.get_me()

        ctx = Context(self.conversations, bot, bot_info)

        if update.get('message'):
            payload = update['message']
            ctx.user = payload['from']
            ctx.chat = payload['chat']
            ctx.reply_id = payload['message_id']

            text = payload['text']
            if (text.startswith('/start ') or
                    text.startswith('/start@%s ' % bot_info['username'].lower())):
                text = text.split(None, 1)[1]
            if not text.startswith('/'):
                tmp = decode(text)
                if tmp.startswith('/'):
                    text = tmp
            if ctx.chat['type'] == 'private':
                prev_text = self.conversations.pop(ctx.user['id'], None)
                if not text.startswith('/') and prev_text:
                    text = '%s %s' % (prev_text, text)
            if text != payload['text']:
                payload['entities'] = []
            ctx.text = text

            return ctx

        if update.get('callback_query'):
            payload = update['callback_query']
            ctx.user = payload['from']
            ctx.chat = payload['message']['chat']
            ctx.edit_id = payload['message']['message_id']
            ctx.text = payload['data']
            return ctx

        if update.get('inline_query'):
            payload = update['inline_query']
            ctx.user = payload['from']
            ctx.answer_id = payload['id']
            ctx.text = payload['query']
            return ctx


class Context(object):
    """Normalized presentation of an incoming message or event.

    This primarily standardizes how the payload text is found (update.message.text,
    update.callback_query.data, update.inline_query.query, etc.) and how replies are sent
    (update.message.reply_text, update.callback_query.message.edit_message_text, bot.send_message,
    etc.).
    """

    # pylint: disable=too-many-instance-attributes
    private = False
    user = chat = text = None
    reply_id = edit_id = answer_id = None

    def __init__(self, conversations, bot, bot_info):
        self._conversations = conversations
        self.bot = bot
        self.bot_info = bot_info

    def encode_link(self, command, text=None):
        """Generate an HTML fragment that links to a deeplink back to the bot."""

        # pylint: disable=deprecated-method
        return '<a href="%s">%s</a>' % (cgi.escape(self.encode_url(command), True), text or command)

    def encode_url(self, command):
        """Generate a deeplink URL."""

        return 'https://t.me/%s?start=%s' % (self.bot_info['username'], encode(command))

    def reply_html(self, text, *args, **kwargs):
        """Reply or edit the context's message with the given HTML fragment."""

        kwargs.setdefault('parse_mode', 'HTML')
        return self.reply_text(text, *args, **kwargs)

    def reply_inline(self, results, **kwargs):
        """Reply or edit the context's message with the given result list."""

        if self.answer_id:
            return self.bot.answer_inline_query(
                inline_query_id=self.answer_id, results=results, **kwargs)

    def reply_markdown(self, text, *args, **kwargs):
        """Reply or edit the context's message with the given Markdown fragment."""

        kwargs.setdefault('parse_mode', 'Markdown')
        return self.reply_text(text, *args, **kwargs)

    def reply_text(self, text, *args, **kwargs):
        """Reply or edit the context's message with the given text."""

        if args:
            text %= args

        if self.reply_id:
            if self.chat['type'] == 'private':
                return self.bot.send_message(chat_id=self.user['id'], text=text, **kwargs)
            if not self.private:
                kwargs.setdefault('reply_to_message_id', self.reply_id)
                return self.bot.send_message(chat_id=self.chat['id'], text=text, **kwargs)
            try:
                return self.bot.send_message(chat_id=self.user['id'], text=text, **kwargs)
            except ntelebot.errors.Unauthorized:
                return self.bot.send_message(
                    chat_id=self.chat['id'],
                    text=self.encode_link(self.text, "Let's take this to a private chat!"),
                    reply_to_message_id=self.reply_id,
                    parse_mode='HTML')
        if self.edit_id:
            return self.bot.edit_message_text(
                chat_id=self.chat['id'], message_id=self.edit_id, text=text, **kwargs)

    def set_conversation(self, text=None):
        """If the next message from this user does not begin with a slash, prepend text."""

        self._conversations[self.user['id']] = text or self.text


def encode(text):
    """Prepare text for use as a Telegram bot deeplink's start= value."""

    if not isinstance(text, bytes):
        text = text.encode('utf-8')

    return base64.urlsafe_b64encode(text).rstrip(b'=')


def decode(text):
    """Extract the original command from a deeplink's start= value."""

    if not isinstance(text, bytes):
        try:
            text = text.encode('ascii')
        except UnicodeEncodeError:
            return ''

    try:
        text = base64.urlsafe_b64decode(text + b'====')
    except (TypeError, ValueError):
        return ''

    try:
        return text.decode('utf-8')
    except UnicodeDecodeError:
        return ''
