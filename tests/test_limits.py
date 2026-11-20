"""Tests for ntelebot.limits."""

import pytest

import ntelebot

IMAGE_URL = 'https://ssl.gstatic.com/calendar/images/eventillustrations/v1/img_pride_2x.jpg'


def test_message_text_length_max(bot_token, bot_test_chat):
    """Verify sendmessage limits haven't changed."""

    bot = ntelebot.bot.Bot(bot_token)
    bot.delete_message.respond(real_http=True)
    bot.send_message.respond(real_http=True)

    message = bot.send_message(chat_id=bot_test_chat,
                               text='a' * ntelebot.limits.message_text_length_max)
    bot.delete_message(chat_id=message['chat']['id'], message_id=message['message_id'])

    with pytest.raises(ntelebot.errors.TooLong):
        bot.send_message(chat_id=bot_test_chat,
                         text='a' * (ntelebot.limits.message_text_length_max + 1))


def test_message_caption_length_max(bot_token, bot_test_chat):
    """Verify sendphoto limits haven't changed."""

    bot = ntelebot.bot.Bot(bot_token)
    bot.delete_message.respond(real_http=True)
    bot.send_photo.respond(real_http=True)

    message = bot.send_photo(chat_id=bot_test_chat,
                             photo=IMAGE_URL,
                             caption='a' * ntelebot.limits.message_caption_length_max)
    bot.delete_message(chat_id=message['chat']['id'], message_id=message['message_id'])

    with pytest.raises(ntelebot.errors.TooLong):
        bot.send_photo(chat_id=bot_test_chat,
                       photo=IMAGE_URL,
                       caption='a' * (ntelebot.limits.message_caption_length_max + 1))


def test_rich_message_length_max(bot_token, bot_test_chat):
    """Verify sendrichmessage limits haven't changed."""

    bot = ntelebot.bot.Bot(bot_token)
    bot.delete_message.respond(real_http=True)
    bot.send_rich_message.respond(real_http=True)

    message = bot.send_rich_message(
        chat_id=bot_test_chat, rich_message={'html': 'a' * ntelebot.limits.rich_message_length_max})
    bot.delete_message(chat_id=message['chat']['id'], message_id=message['message_id'])

    with pytest.raises(ntelebot.errors.TooLong):
        bot.send_rich_message(
            chat_id=bot_test_chat,
            rich_message={'html': 'a' * (ntelebot.limits.rich_message_length_max + 1)})
