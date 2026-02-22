"""Shim — all signal logic lives in life.signal."""

from life.signal import (
    get_conversations,
    get_message,
    get_messages,
    link_device as link,
    list_accounts,
    list_contacts_for as list_contacts,
    list_groups,
    mark_read,
    receive,
    reply_to as reply,
    send_group,
    send_to as send,
    test_connection,
)

__all__ = [
    "get_conversations",
    "get_message",
    "get_messages",
    "link",
    "list_accounts",
    "list_contacts",
    "list_groups",
    "mark_read",
    "receive",
    "reply",
    "send",
    "send_group",
    "test_connection",
]
