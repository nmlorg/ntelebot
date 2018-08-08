"""A quick bot that echoes all messages sent to it."""

from __future__ import absolute_import, division, print_function, unicode_literals

import pprint
import sys

import ntelebot


def main(argv):  # pylint: disable=missing-docstring
    if len(argv) != 2:
        print('Usage: %s BOT:TOKEN' % argv[0])
        print()
        print('Where BOT:TOKEN is a code received from following the process at '
              'https://core.telegram.org/bots#creating-a-new-bot.')
        return 1

    bot = ntelebot.bot.Bot(argv[1])

    pprint.pprint(bot.get_me())

    offset = None
    while True:
        updates = bot.get_updates(offset=offset, timeout=10)
        if updates:
            offset = updates[-1]['update_id'] + 1
            for update in updates:
                pprint.pprint(update)
                if update.get('message'):
                    message = update['message']
                    bot.send_message(
                        chat_id=message['chat']['id'],
                        text='\U0001f50a ' + message['text'],
                        reply_to_message_id=message['message_id'])


if __name__ == '__main__':
    sys.exit(main(sys.argv))
