import re

from lib import niiloism

NICK_REGEX = re.compile(r'(?i)^[a-z_\-\[\]\\^{}|`]'
                        r'[a-z0-9_\-\[\]\\^{}|`]{2,15}$')
ISUPPORT_LINE_LENGTH_KEYS = ("LINELEN", "MAXLINE", "MAXLINELEN", "MSGLEN")
DEFAULT_IRC_LINE_LENGTH_BYTES = 512


def get_quit_message():
    try:
        message = niiloism.random_word()
    except Exception:
        # Fallback to make sure this never fails
        message = "Quitting"
    return message


def is_valid_nick(string):
    return NICK_REGEX.match(string)


def get_server_line_limit_bytes(connection):
    features = getattr(connection, "features", None)
    if features is None:
        return DEFAULT_IRC_LINE_LENGTH_BYTES

    for key in ISUPPORT_LINE_LENGTH_KEYS:
        value = None
        if hasattr(features, "get") or isinstance(features, dict):
            value = features.get(key) or features.get(key.lower())
        else:
            value = getattr(features, key, None) or getattr(features, key.lower(), None)
        if value is None:
            continue

        match = re.search(r"\d+", str(value))
        if not match:
            continue

        limit = int(match.group(0))
        if limit > 0:
            return limit

    return DEFAULT_IRC_LINE_LENGTH_BYTES


def get_max_privmsg_text_bytes(target, line_limit_bytes):
    # Clients send: "PRIVMSG <target> :<text>\r\n"
    overhead = len(f"PRIVMSG {target} :\r\n".encode())
    return max(1, line_limit_bytes - overhead)


def split_privmsg_text(text, max_bytes):
    if max_bytes <= 0:
        return [text]
    if len(text.encode("utf-8")) <= max_bytes:
        return [text]

    chunks = []
    remaining = text

    while remaining:
        if len(remaining.encode("utf-8")) <= max_bytes:
            chunks.append(remaining)
            break

        split_idx = _max_prefix_index_by_bytes(remaining, max_bytes)
        soft_idx = remaining.rfind(" ", 0, split_idx + 1)
        if soft_idx > 0:
            current = remaining[:soft_idx].rstrip()
            next_remaining = remaining[soft_idx + 1:].lstrip()
        else:
            current = remaining[:split_idx]
            next_remaining = remaining[split_idx:]

        if not current:
            # Defensive fallback for pathological whitespace-only data.
            current = remaining[:split_idx]
            next_remaining = remaining[split_idx:]

        chunks.append(current)
        remaining = next_remaining

    return chunks


def split_privmsg_text_limited(text, max_bytes, max_chunks):
    if max_chunks <= 0:
        max_chunks = 1

    chunks = split_privmsg_text(text, max_bytes)
    if len(chunks) <= max_chunks:
        return chunks, False

    sent_chunks = chunks[:max_chunks - 1]
    remaining_text = " ".join(chunks[max_chunks - 1:])
    last_chunk = split_privmsg_text(remaining_text, max_bytes)[0]
    sent_chunks.append(last_chunk)
    return sent_chunks, True


def _max_prefix_index_by_bytes(text, max_bytes):
    used_bytes = 0
    for index, char in enumerate(text):
        char_bytes = len(char.encode("utf-8"))
        if used_bytes + char_bytes > max_bytes:
            return max(1, index)
        used_bytes += char_bytes
    return len(text)
