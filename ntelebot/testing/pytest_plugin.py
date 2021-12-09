import pytest

import ntelebot.testing.adapter
import ntelebot.testing.telegram


@pytest.fixture
def telegram(monkeypatch):
    _telegram = ntelebot.testing.telegram.Telegram()
    adapter = ntelebot.testing.adapter.Adapter(_telegram)
    monkeypatch.setattr('requests.Session.get_adapter', lambda self, url: adapter)
    return _telegram
