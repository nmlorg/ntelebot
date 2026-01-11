"""Utilities related to https://core.telegram.org/bots#deep-linking."""

import base64
import html


def decode(text):
    """Extract the original command from a deeplink's start= value."""

    if not isinstance(text, bytes):
        try:
            text = text.encode('ascii')
        except UnicodeEncodeError:
            return ''

    try:
        text = base64.urlsafe_b64decode(text + b'====')
    except (TypeError, ValueError):
        return ''

    try:
        return text.decode('utf-8')
    except UnicodeDecodeError:
        return ''


def encode(text):
    """Prepare text for use as a Telegram bot deeplink's start= value."""

    if not isinstance(text, bytes):
        text = text.encode('utf-8')

    return base64.urlsafe_b64encode(text).rstrip(b'=').decode('ascii')


def encode_link(username, command, text=None):
    """Generate an HTML fragment that links to a deeplink back to the bot."""

    return f'<a href="{html.escape(encode_url(username, command))}">{text or command}</a>'


def encode_url(username, command):
    """Generate a deeplink URL."""

    return f'https://t.me/{username}?start={encode(command)}'
