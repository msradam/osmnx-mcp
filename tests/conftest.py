"""Pytest configuration and global patches."""

import claude_code_sdk._internal.client as _sdk_client
import claude_code_sdk._internal.message_parser as _mp
from claude_code_sdk._errors import MessageParseError
from claude_code_sdk.types import SystemMessage

_original_parse_message = _mp.parse_message


def _patched_parse_message(data):
    msg_type = data.get("type") if isinstance(data, dict) else None
    try:
        return _original_parse_message(data)
    except MessageParseError:
        # Unknown types (e.g. rate_limit_event) are treated as SystemMessage so
        # the async-for in query() continues rather than aborts.
        return SystemMessage(subtype=msg_type or "unknown", data=data)


# Patch both the module attribute and the already-imported reference in client.py
_mp.parse_message = _patched_parse_message
_sdk_client.parse_message = _patched_parse_message
