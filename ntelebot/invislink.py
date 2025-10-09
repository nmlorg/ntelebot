"""Quick implementation of https://github.com/nmlorg/metabot/issues/1."""

import base64
import json


def _decode_text(text):
    try:
        return base64.urlsafe_b64decode(text.encode('ascii')).decode('utf-8')
    except (UnicodeEncodeError, base64.binascii.Error):
        pass


def _encode_text(data):
    return base64.urlsafe_b64encode(data.encode('utf-8')).decode('ascii')


def _decode_list(text):
    text = _decode_text(text)
    if text:
        return text.split('\0')


def _encode_list(data):
    return _encode_text('\0'.join(data))


def _decode_dict(text):
    data = _decode_list(text)
    return dict(zip(data[::2], data[1::2]))


def _encode_dict(data):
    flat = []
    for k, v in data.items():
        flat.append(str(k))
        flat.append(str(v))
    return _encode_list(flat)


def _decode_json(text):
    try:
        return json.loads(_decode_text(text))
    except json.decoder.JSONDecodeError:
        pass


def _encode_json(data):
    return _encode_text(json.dumps(data, ensure_ascii=False, separators=(',', ':'), sort_keys=True))


def decode(entities):
    """Extract metadata hidden inside invisible links."""

    btn = meta = None

    for entity in entities:
        if entity['type'] == 'text_link':
            url = entity['url']
            if url.startswith('tg://btn/'):
                btn = _decode_list(url[len('tg://btn/'):])
            elif url.startswith('tg://meta/'):
                meta = _decode_json(url[len('tg://meta/'):])
                if not isinstance(meta, dict):
                    meta = None
            if btn and meta:
                break

    return btn, meta


def encode(btn, meta):
    """Hide metadata inside invisible links."""

    text = ''
    if btn:
        text = f'{text}<a href="tg://btn/{_encode_list(btn)}">\u200b</a>'
    if meta:
        text = f'{text}<a href="tg://meta/{_encode_json(meta)}">\u200b</a>'
    return text
