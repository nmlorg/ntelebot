"""Quick implementation of https://github.com/nmlorg/metabot/issues/1."""

import re


def combine(prefixes, text):
    """Convert '\0idx\0suffix' to prefixes[int(idx)] + 'suffix'."""

    ret = re.match('^\0([0-9]+)\0(.*)$', text)
    if not ret:
        return text
    index, suffix = ret.groups()
    index = int(index)
    if index < len(prefixes):
        return prefixes[index] + suffix
    return text


def fix(keyboard, maxlen=64):
    """Encode the callback_data of any buttons in keyboard that exceed Telegram's max length."""

    broken = []
    for row in keyboard:
        for button in row:
            if len(button['callback_data']) > maxlen:
                broken.append(button)
    if not broken:
        return
    prefixes, mapping = shorten_lines((button['callback_data'] for button in broken), maxlen)
    for button in broken:
        button['callback_data'] = mapping[button['callback_data']]
    return prefixes


def shorten_lines(lines, maxlen):
    """Generate a list of shared prefixes and a map of long string -> encoded string."""

    prefixes = []
    mapping = {}
    for line in sorted(lines, key=lambda line: -len(line)):
        if len(line) <= maxlen:
            # This could be moved into the else: below to minimize overall payload size, but leaving
            # lines that are already within the limit as is allows more buttons to remain functional
            # if a message's entities section is ever trimmed.
            break
        for i, prefix in enumerate(prefixes):
            if line.startswith(prefix):
                break
        else:
            i = len(prefixes)
            prefixcode = f'\0{i}\0'
            # The new prefix will be as small as possible so the remaining line--including the
            # encoded prefix number--is exactly maxlen bytes long. This should guarantee the maximum
            # possible reuse between lines.
            prefix = line[:-(maxlen - len(prefixcode))]
            prefixes.append(prefix)
        mapping[line] = f'\0{i}\0{line[len(prefix):]}'
    return prefixes, mapping
