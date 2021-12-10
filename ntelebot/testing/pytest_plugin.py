import pytest

import ntelebot.testing.adapter
import ntelebot.testing.botapi
import ntelebot.testing.telegram


@pytest.fixture
def telegram(monkeypatch):
    _telegram = ntelebot.testing.telegram.Telegram()
    botapi = ntelebot.testing.botapi.BotAPI(_telegram)
    adapter = ntelebot.testing.adapter.Adapter(_telegram, botapi)
    monkeypatch.setattr('requests.Session.get_adapter', lambda self, url: adapter)
    return _telegram
