import pytest

import ntelebot


def test_send_message(telegram):
    serverbot1234 = telegram.create_bot(1234)
    bot1234 = ntelebot.bot.Bot(f'1234:{serverbot1234.token}')

    # User 1000 does not exist.
    with pytest.raises(ntelebot.errors.BadRequest):
        bot1234.send_message(chat_id=1000, text='Should fail')

    user1000 = telegram.create_user(1000)
    # User 1000 does not have a chat open with bot 1234.
    with pytest.raises(ntelebot.errors.Forbidden):
        bot1234.send_message(chat_id=1000, text='Should fail')

    telegram.create_private_chat(1000, 1234)

    assert bot1234.send_message(chat_id=1000, text='Should succeed') == {
        'chat': {
            'first_name': 'User',
            'id': 1000,
            'last_name': '1000',
            'type': 'private',
            'username': 'user1000',
        },
        'date': 66000010,
        'from': {
            'first_name': 'Test Bot 1234',
            'id': 1234,
            'is_bot': True,
            'username': 'test1234bot',
        },
        'message_id': 77001,
        'text': 'Should succeed',
    }

    user1000.about['first_name'] = 'Tester'
    serverbot1234.about['first_name'] = 'Test Robot'

    assert bot1234.send_message(chat_id=1000, text='Should also succeed') == {
        'chat': {
            'first_name': 'Tester',
            'id': 1000,
            'last_name': '1000',
            'type': 'private',
            'username': 'user1000',
        },
        'date': 66000020,
        'from': {
            'first_name': 'Test Robot',
            'id': 1234,
            'is_bot': True,
            'username': 'test1234bot',
        },
        'message_id': 77002,
        'text': 'Should also succeed',
    }
