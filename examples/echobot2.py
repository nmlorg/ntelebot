"""A version of echobot1.py that uses ntelebot.loop.Loop.

This is just offered as a form of documentation; it is much simpler to avoid using Loop unless you
have a good reason to use an explicit dispatcher.
"""

import pprint
import sys

import ntelebot


def dispatch(bot, update):
    """Print all updates and echo back all messages."""

    pprint.pprint(update)
    if update.get('message'):
        message = update['message']
        bot.send_message(chat_id=message['chat']['id'],
                         text='\U0001f50a ' + message['text'],
                         reply_to_message_id=message['message_id'])


def main(argv):  # pylint: disable=missing-docstring
    if len(argv) < 2:
        print('Usage: %s BOT:TOKEN [BOT:TOKEN [BOT:TOKEN [...]]]' % argv[0])
        print()
        print('Where BOT:TOKEN is one or more codes received from following the process at '
              'https://core.telegram.org/bots#creating-a-new-bot.')
        return 1

    loop = ntelebot.loop.Loop()

    for token in argv[1:]:
        bot = ntelebot.bot.Bot(token)
        pprint.pprint(bot.get_me())
        loop.add(bot, dispatch)

    loop.run()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
