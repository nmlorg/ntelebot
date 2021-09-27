"""A version of echobot3.py that uses ntelebot.dispatch.LoopDispatcher."""

import pprint
import sys

import ntelebot


def echo(ctx):
    """Print and echo back all messages."""

    pprint.pprint(ctx.__dict__)
    ctx.reply_text('\U0001f50a ' + ctx.text)


def main(argv):  # pylint: disable=missing-docstring
    if len(argv) < 2:
        print(f'Usage: {argv[0]} BOT:TOKEN [BOT:TOKEN [BOT:TOKEN [...]]]')
        print()
        print('Where BOT:TOKEN is one or more codes received from following the process at '
              'https://core.telegram.org/bots#creating-a-new-bot.')
        return 1

    loop = ntelebot.loop.Loop()
    dispatcher = ntelebot.dispatch.LoopDispatcher()

    dispatcher.add(echo)

    for token in argv[1:]:
        bot = ntelebot.bot.Bot(token)
        pprint.pprint(bot.get_me())
        loop.add(bot, dispatcher)

    loop.run()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
