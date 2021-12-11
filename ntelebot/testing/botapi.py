class BotAPI:

    def __init__(self, telegram):
        self._telegram = telegram

    @staticmethod
    def api_echoparams(unused_bot, **kwargs):
        kwargs['count'] = len(kwargs)
        return kwargs

    @staticmethod
    def api_getme(bot):
        me = {}
        me.update(bot.conf)
        me.update(bot.about)
        return me

    def api_sendmessage(self, bot, chat_id=None, text=None, **unused_kwargs):
        try:
            view = self._telegram.get_chat_view(bot, chat_id)
        except self._telegram.CanNotSend as exc:
            raise self.Error(403, "Forbidden: bot can't initiate conversation with a user") from exc
        except self._telegram.ChatNotFound as exc:
            raise self.Error(400, 'Bad Request: chat not found') from exc

        return view.send_message(text)

    class Error(Exception):
        pass
