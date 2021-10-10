"""A version of echobot2.py that uses ntelebot.preprocess.Preprocessor."""

import pprint
import sys

import ntelebot


class Dispatcher:  # pylint: disable=too-few-public-methods
    """Print all updates and echo back all messages."""

    def __init__(self):
        self.preprocessor = ntelebot.preprocess.Preprocessor()

    def __call__(self, bot, update):
        ctx = self.preprocessor(bot, update)
        if ctx:
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
    dispatcher = Dispatcher()

    for token in argv[1:]:
        bot = ntelebot.bot.Bot(token)
        pprint.pprint(bot.get_me())
        loop.add(bot, dispatcher)

    loop.run()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
