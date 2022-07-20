"""hooks, filters and commands definitions."""
from urllib.error import HTTPError

import simplebot
from deltachat import Message
from simplebot.bot import DeltaBot, Replies

from .templates import template
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
    desc = f"""change settings of the given mailing list.

    /{prefix}settings mylist.example.com advertised False
    """
    bot.commands.register(func=settings_cmd, name=f"/{prefix}settings", admin=True)
    desc = f"""create a new mailing list.

    /{prefix}create legacy-announce mychannel@example.com My Channel
    """
    bot.commands.register(
        func=create_cmd, name=f"/{prefix}create", help=desc, admin=True
    )


def list_cmd(bot: DeltaBot, replies: Replies) -> None:
    """show the list of public super groups and channels."""

    def get_list(bot_addr: str, chats: list) -> str:
        return template.render(
            bot_addr=bot_addr,
            prefix=get_default(bot, "command_prefix", ""),
            chats=chats,
        )

    client = get_client(bot)
    groups, channels = [], []
    for mailinglist in client.get_lists(advertised=True):
        settings = mailinglist.settings
        mlist = (
            mailinglist.list_id,
            mailinglist.display_name,
            settings["info"],
            (settings["last_post_at"] or "").split("T")[0],
            mailinglist.member_count,
        )
        if settings["allow_list_posts"]:
            groups.append(mlist)
        else:
            channels.append(mlist)

    if groups:
        groups.sort(key=lambda g: g[-1], reverse=True)
        text = f"⬇️ Super Groups ({len(groups)}) ⬇️"
        replies.add(text=text, html=get_list(bot.self_contact.addr, groups))

    if channels:
        channels.sort(key=lambda c: c[-1], reverse=True)
        text = f"⬇️ Channels ({len(channels)}) ⬇️"
        replies.add(text=text, html=get_list(bot.self_contact.addr, channels))

    if not groups and not channels:
        replies.add(text="❌ Empty List")


def join_cmd(bot: DeltaBot, payload: str, message: Message, replies: Replies) -> None:
    """join the given super group or channel."""
    client = get_client(bot)
    try:
        mlist = client.get_list(payload)
        addr = message.get_sender_contact().addr
        mlist.subscribe(
            addr, pre_verified=True, pre_confirmed=True, send_welcome_message=True
        )
    except HTTPError as ex:
        bot.logger.exception(ex)
        replies.add(text="❌ Invalid ID", quote=message)


def leave_cmd(bot: DeltaBot, payload: str, message: Message, replies: Replies) -> None:
    """leave the given super group or channel."""
    client = get_client(bot)
    try:
        mlist = client.get_list(payload)
        mlist.unsubscribe(message.get_sender_contact().addr)
    except ValueError as ex:
        bot.logger.exception(ex)
        replies.add(text="❌ You are not a member of that group/channel", quote=message)
    except HTTPError as ex:
        bot.logger.exception(ex)
        replies.add(text="❌ Invalid ID", quote=message)


def create_cmd(bot: DeltaBot, payload: str, message: Message, replies: Replies) -> None:
    try:
        mltype, mladdr, mlname = payload.split(maxsplit=2)
        client = get_client(bot)
        domain = client.get_domain(get_default(bot, "domain", ""))
        if mltype == "channel":
            mltype = "legacy-announce"
        elif mltype == "group":
            mltype = "legacy-default"
        mlist = domain.create_list(mladdr, style_name=mltype)
        settings = mlist.settings
        settings["display_name"] = mlname
        settings["description"] = mlname
        settings["default_nonmember_action"] = "reject"
        settings.save()
        mlist.unsubscribe(message.get_sender_contact().addr)
    except Exception as ex:
        bot.logger.exception(ex)
        replies.add(text=f"❌ Failed to create mailing list: {ex}", quote=message)


def settings_cmd(
    bot: DeltaBot, payload: str, message: Message, replies: Replies
) -> None:
    try:
        mlid, *args = payload.split(maxsplit=2)
        key = args[0]
        value = args[1] if len(args) == 2 else None
        client = get_client(bot)
        mlist = client.get_list(mlid)
        settings = mlist.settings
        if value is None:
            value = settings[key]
        else:
            settings[key] = value
            settings.save()
        replies.add(text=f"{key}={value!r}", quote=message)
    except Exception as ex:
        bot.logger.exception(ex)
        replies.add(text=f"❌ Error: {ex}", quote=message)
