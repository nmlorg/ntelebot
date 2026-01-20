"""Non-universal, but fairly versatile update preprocessor."""

import threading

import ntelebot

PRIVATE_RESPONSE_TEXT = """\
That's too noisy to answer here. I tried to reply in private, but I can only send you a message \
if you already have a private chat open with me\u2026 and it looks like you don't \U0001f61e

Click my name/picture, then the \U0001f4ac icon, then retype your command there; or click the \
button below and your Telegram app will do all that automatically.

(I'll delete this in a minute.)"""


class Preprocessor:  # pylint: disable=too-few-public-methods
    """Non-universal, but fairly versatile update preprocessor."""

    def __init__(self):
        self.conversations = {}

    def __call__(self, bot, update):  # pylint: disable=too-many-branches,too-many-statements
        """Convert a Telegram Update instance into a normalized Context."""

        ctx = Context(self.conversations, bot)

        payload = update.get('message') or update.get('channel_post')

        if payload:
            ctx.user = payload.get('from')
            ctx.chat = payload['chat']
            ctx.reply_id = payload['message_id']

            if (new_chat_members := payload.get('new_chat_members')):
                ctx.type = 'join'
                ctx.data = new_chat_members
                return ctx

            if (pinned_message := payload.get('pinned_message')):
                ctx.type = 'pin'
                ctx.data = pinned_message
                return ctx

            ctx.type = 'message'

            if payload.get('forward_date'):
                ctx.forwarded = True
                text = ''
                if payload.get('forward_from'):
                    ctx.forward_from = payload['forward_from']['id']
            else:
                text = payload.get('text', '')
                if payload.get('reply_to_message'):
                    ctx.reply_from = payload['reply_to_message']['from']['id']

            if text.startswith('/start ') or text.startswith(f'/start@{bot.username.lower()} '):
                text = text.split(None, 1)[1]
            if not text.startswith('/'):
                tmp = ntelebot.deeplink.decode(text)
                if tmp.startswith('/'):
                    text = tmp
            if ctx.user and ctx.chat['type'] == 'private':
                prev_text = self.conversations.pop(ctx.user['id'], None)
                if not text.startswith('/') and prev_text:
                    text = text and f'{prev_text} {text}' or prev_text
            if text != payload.get('text', ''):
                payload['entities'] = []
            ctx.command, ctx.text = get_command(text, bot.username)
            ctx.prefix = ctx.text.partition(' ')[0]

            if payload.get('document'):
                ctx.document = payload['document']['file_id']

            if payload.get('photo'):
                size = 0
                for photo in payload['photo']:
                    if size < photo['height'] * photo['width']:
                        size = photo['height'] * photo['width']
                        ctx.photo = photo['file_id']

            if payload.get('sticker'):
                ctx.sticker = payload['sticker']['file_id']

            return ctx

        if update.get('callback_query'):
            payload = update['callback_query']
            ctx.type = 'callback_query'
            ctx.user = payload['from']
            ctx.chat = payload['message']['chat']
            ctx.edit_id = payload['message']['message_id']
            ctx.callback_id = payload['id']
            text = payload['data']
            if (entities := payload['message'].get('entities')):
                prefixes, meta = ntelebot.invislink.decode(entities)
                if prefixes:
                    text = ntelebot.keyboardutil.combine(prefixes, text)
                if meta:
                    ctx.meta = meta
            ctx.command, ctx.text = get_command(text, bot.username)
            ctx.prefix = ctx.text.partition(' ')[0]
            return ctx

        if update.get('inline_query'):
            payload = update['inline_query']
            ctx.type = 'inline_query'
            ctx.user = payload['from']
            ctx.answer_id = payload['id']
            ctx.text = payload['query']
            ctx.prefix = ctx.text.partition(' ')[0]
            return ctx


class Context:
    """Normalized presentation of an incoming message or event.

    This primarily standardizes how the payload text is found (update.message.text,
    update.callback_query.data, update.inline_query.query, etc.) and how replies are sent
    (update.message.reply_text, update.callback_query.message.edit_message_text, bot.send_message,
    bot.answer_inline_query, etc.).
    """

    # pylint: disable=too-many-instance-attributes
    private = False
    type = user = chat = text = prefix = command = data = None
    forwarded = False
    forward_from = reply_from = None
    document = photo = sticker = None
    reply_id = edit_id = answer_id = None
    callback_id = None

    def __init__(self, conversations, bot):
        self._conversations = conversations
        self.bot = bot
        self.meta = {}

    def forward(self, chat_id, **kwargs):
        """Forward the incoming message to the target chat."""

        return self.bot.forward_message(chat_id=chat_id,
                                        from_chat_id=self.chat['id'],
                                        message_id=self.reply_id,
                                        **kwargs)

    def reply_html(self, text, *args, **kwargs):
        """Reply or edit the context's message with the given HTML fragment."""

        kwargs.setdefault('parse_mode', 'HTML')
        return self.reply_text(text, *args, **kwargs)

    def reply_inline(self, results, **kwargs):
        """Reply or edit the context's message with the given result list."""

        if self.answer_id:
            return self.bot.answer_inline_query(inline_query_id=self.answer_id,
                                                results=results,
                                                **kwargs)

    def reply_markdown(self, text, *args, **kwargs):
        """Reply or edit the context's message with the given Markdown fragment."""

        kwargs.setdefault('parse_mode', 'Markdown')
        return self.reply_text(text, *args, **kwargs)

    def reply_text(self, text, *args, **kwargs):  # pylint: disable=too-many-branches
        """Reply or edit the context's message with the given text."""

        if args:
            text %= args

        if kwargs.get('parse_mode') == 'HTML':
            prefixes = None
            if kwargs.get('reply_markup') and kwargs['reply_markup'].get('inline_keyboard'):
                prefixes = ntelebot.keyboardutil.fix(kwargs['reply_markup']['inline_keyboard'])
            text = f'{ntelebot.invislink.encode(prefixes, self.meta)}{text}'

        if self.reply_id:
            if text.startswith('document:'):
                method = self.bot.send_document
                kwargs.update(zip(('document', 'caption'), text[len('document:'):].split(None, 1)))
            elif text.startswith('photo:'):
                method = self.bot.send_photo
                kwargs.update(zip(('photo', 'caption'), text[len('photo:'):].split(None, 1)))
            elif text.startswith('sticker:') and ' ' not in text:
                method = self.bot.send_sticker
                kwargs['sticker'] = text[len('sticker:'):]
            else:
                method = self.bot.send_message
                kwargs['text'] = text

            if self.user and self.chat['type'] == 'private':
                return method(chat_id=self.user['id'], **kwargs)

            reply_parameters = {
                'message_id': self.reply_id,
                'chat_id': self.chat['id'],
                'allow_sending_without_reply': True,
            }

            if not self.private or not self.user:
                return method(chat_id=self.chat['id'], reply_parameters=reply_parameters, **kwargs)

            try:
                message = method(chat_id=self.user['id'],
                                 reply_parameters=reply_parameters,
                                 **kwargs)
                self.bot.send_message(chat_id=self.chat['id'],
                                      text='(I replied in private.)',
                                      reply_parameters=reply_parameters)
                return message
            except ntelebot.errors.Forbidden:
                orig_text = self.text
                if self.command:
                    orig_text = f'/{self.command} {orig_text}'
                keyboard = [[{
                    'text': f'Resend {repr(orig_text)} in private',
                    'url': self.bot.encode_url(orig_text),
                }]]
                message = self.bot.send_message(chat_id=self.chat['id'],
                                                text=PRIVATE_RESPONSE_TEXT,
                                                reply_parameters=reply_parameters,
                                                reply_markup={'inline_keyboard': keyboard})
                thr = threading.Timer(60,
                                      self.bot.delete_message,
                                      kwargs={
                                          'chat_id': self.chat['id'],
                                          'message_id': message['message_id']
                                      })
                thr.daemon = True
                thr.start()
                return message

        if self.edit_id:
            return self.bot.edit_message_text(chat_id=self.chat['id'],
                                              message_id=self.edit_id,
                                              text=text,
                                              **kwargs)

    def set_conversation(self, text):
        """If the next message from this user does not begin with a slash, prepend text."""

        if not text.startswith('/') and self.command:
            text = f'/{self.command} {text}'
        self._conversations[self.user['id']] = text

    def split(self, num):
        """Split self.text into exactly num pieces, substituting blank strings for empty slots.

        This is intended for something like:

            def handler(ctx):
                target, action, text = ctx.split(3)

        where a message containing '/command' would result in target = action = text = '',
        '/command mytarget' would have target = 'mytarget' and action = text = '',
        '/command mytarget add some more data' would have target = 'mytarget', action = 'add', and
        text = 'some more data'.
        """

        ret = self.text.split(None, num - 1)
        while len(ret) < num:
            ret.append('')
        return ret


def get_command(text, username):
    """The normalized command name if this is a command addressed to this bot."""

    if not text.startswith('/'):
        return None, text

    command, _, rest = text[1:].partition(' ')
    command = command.lower()
    if '@' in command:
        command, target_username = command.split('@', 1)
        if target_username != username.lower():
            return None, text
    return command, rest.lstrip()
