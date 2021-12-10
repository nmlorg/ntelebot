class BotAPI:

    def __init__(self, telegram):
        self._telegram = telegram

    @staticmethod
    def api_echoparams(unused_bot, **kwargs):
        kwargs['count'] = len(kwargs)
        return kwargs

    @staticmethod
    def api_getme(bot):
        return bot.conf
