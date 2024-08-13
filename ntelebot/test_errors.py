"""Tests for ntelebot.errors (as used by ntelebot.bot)."""

import pytest

import ntelebot


def test_unmodified(bot_token, bot_test_chat):
    """Verify we capture MESSAGE_NOT_MODIFIED properly."""

    bot = ntelebot.bot.Bot(bot_token)
    bot.delete_message.respond(real_http=True)
    bot.edit_message_text.respond(real_http=True)
    bot.send_message.respond(real_http=True)

    initial = 'test_unmodified initial'
    message1 = bot.send_message(chat_id=bot_test_chat, text=initial)
    assert message1['text'] == initial

    edited = 'test_unmodified edited'
    message2 = bot.edit_message_text(chat_id=bot_test_chat,
                                     message_id=message1['message_id'],
                                     text=edited)
    assert message2['text'] == edited

    with pytest.raises(ntelebot.errors.Unmodified):
        bot.edit_message_text(chat_id=bot_test_chat, message_id=message1['message_id'], text=edited)

    assert bot.delete_message(chat_id=bot_test_chat, message_id=message1['message_id'])
