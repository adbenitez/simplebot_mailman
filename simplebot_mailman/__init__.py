"""hooks, filters and commands definitions."""
from urllib.error import HTTPError

import simplebot
from deltachat import Message
from simplebot.bot import DeltaBot, Replies

from .util import get_client, get_default


@simplebot.hookimpl
def deltabot_init(bot: DeltaBot) -> None:
    get_default(bot, "api_url", "http://localhost:8001/3.1/")
    get_default(bot, "api_username", "restadmin")
    get_default(bot, "api_password", "")
    get_default(bot, "domain", "example.com")

    prefix = get_default(bot, "command_prefix", "")

    bot.commands.register(func=list_cmd, name=f"/{prefix}list")
    bot.commands.register(func=join_cmd, name=f"/{prefix}join")
    bot.commands.register(func=leave_cmd, name=f"/{prefix}leave")


def list_cmd(bot: DeltaBot, replies: Replies) -> None:
    """show the list of public groups and channels."""
    prefix = get_default(bot, "command_prefix", "")
    client = get_client(bot)
    text = ""
    for ml in client.get_lists():
        description = ml.settings["info"]
        text += f"{ml.display_name}:\nMembers: {ml.member_count}\nDescription: {description}\nJoin: /{prefix}join_{ml.list_id}\nLeave: /{prefix}leave_{ml.list_id}\n\n"
    replies.add(text=text or "❌ Empty list")


def join_cmd(bot: DeltaBot, payload: str, message: Message, replies: Replies) -> None:
    """join the given group or channel."""
    client = get_client(bot)
    try:
        ml = client.get_list(payload)
        addr = message.get_sender_contact().addr
        ml.subscribe(
            addr, pre_verified=True, pre_confirmed=True, send_welcome_message=True
        )
    except HTTPError as ex:
        bot.logger.exception(ex)
        replies.add(text="❌ Invalid ID", quote=message)


def leave_cmd(bot: DeltaBot, payload: str, message: Message, replies: Replies) -> None:
    """leave the given group or channel."""
    client = get_client(bot)
    try:
        ml = client.get_list(payload)
        ml.unsubscribe(message.get_sender_contact().addr)
    except ValueError as ex:
        bot.logger.exception(ex)
        replies.add(text="❌ You are not a member of that group/channel", quote=message)
    except HTTPError as ex:
        bot.logger.exception(ex)
        replies.add(text="❌ Invalid ID", quote=message)
