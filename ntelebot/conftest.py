"""Test environment defaults."""

import pytest

import ntelebot


@pytest.fixture(autouse=True)
def _bot_mock(monkeypatch, requests_mock):
    requests_mock.case_sensitive = True

    class MockRequest(ntelebot.bot._Request):
        # pylint: disable=missing-docstring,protected-access,too-few-public-methods

        def respond(self, **response):
            requests_mock.post(self.url, **response)

    monkeypatch.setattr('ntelebot.bot._Request', MockRequest)
