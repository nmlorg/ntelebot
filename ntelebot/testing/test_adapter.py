import pytest
import requests

import ntelebot
import ntelebot.testing.adapter


def test_adapter(telegram):
    with pytest.raises(ntelebot.testing.adapter.NoMockAddress):
        requests.get('https://www.example.com')

    resp = requests.get('https://api.telegram.org/bot1234:BoGuS/bogusmethod')
    assert resp.status_code == 401
    assert resp.json() == {'ok': False, 'error_code': 401, 'description': 'Unauthorized'}

    with pytest.raises(ntelebot.errors.Unauthorized):
        ntelebot.bot.Bot('1234:BoGuS').bogus_method()

    assert telegram.create_bot(1234) == 'MTIzNA'

    resp = requests.get('https://api.telegram.org/bot1234:BoGuS/bogusmethod')
    assert resp.status_code == 401
    assert resp.json() == {'ok': False, 'error_code': 401, 'description': 'Unauthorized'}

    with pytest.raises(ntelebot.errors.Unauthorized):
        ntelebot.bot.Bot('1234:BoGuS').bogus_method()

    resp = requests.get('https://api.telegram.org/bot1234:MTIzNA/bogusmethod')
    assert resp.status_code == 404
    assert resp.json() == {'ok': False, 'error_code': 404, 'description': 'Not Found'}

    with pytest.raises(ntelebot.errors.NotFound):
        ntelebot.bot.Bot('1234:MTIzNA').bogus_method()

    resp = requests.get('https://api.telegram.org/bot1234:MTIzNA/getme')
    assert resp.status_code == 200
    assert resp.json() == {
        'ok': True,
        'result': {
            'can_join_groups': True,
            'can_read_all_group_message': False,
            'first_name': 'test1234',
            'id': 1234,
            'is_bot': True,
            'supports_inline_queries': False,
            'username': 'test1234bot',
        }
    }

    assert ntelebot.bot.Bot('1234:MTIzNA').get_me() == {
        'can_join_groups': True,
        'can_read_all_group_message': False,
        'first_name': 'test1234',
        'id': 1234,
        'is_bot': True,
        'supports_inline_queries': False,
        'username': 'test1234bot',
    }
