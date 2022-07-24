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
    bot.commands.register(func=listban_cmd, name=f"/{prefix}banUser")
    bot.commands.register(func=listunban_cmd, name=f"/{prefix}unbanUser")
    bot.commands.register(func=name_cmd, name=f"/{prefix}name")
    bot.commands.register(func=topic_cmd, name=f"/{prefix}topic")
    bot.commands.register(func=link_cmd, name=f"/{prefix}link", admin=True)
    bot.commands.register(func=unlink_cmd, name=f"/{prefix}unlink", admin=True)
    bot.commands.register(func=roles_cmd, name=f"/{prefix}roles", admin=True)
    bot.commands.register(func=siteban_cmd, name=f"/{prefix}globalBan", admin=True)
    bot.commands.register(func=siteunban_cmd, name=f"/{prefix}globalUnban", admin=True)
    bot.commands.register(func=add_member_cmd, name=f"/{prefix}add_member", admin=True)
    bot.commands.register(
        func=remove_member_cmd, name=f"/{prefix}remove_member", admin=True
    )
    bot.commands.register(func=add_owner_cmd, name=f"/{prefix}add_owner", admin=True)
    bot.commands.register(
        func=remove_owner_cmd, name=f"/{prefix}remove_owner", admin=True
    )
    bot.commands.register(
        func=add_moderator_cmd, name=f"/{prefix}add_moderator", admin=True
    )
    bot.commands.register(
        func=remove_moderator_cmd, name=f"/{prefix}remove_moderator", admin=True
    )
    desc = f"""change settings of the given mailing list.

    /{prefix}settings mylist.example.com advertised False
    """
    bot.commands.register(
        func=settings_cmd, name=f"/{prefix}settings", help=desc, admin=True
    )
    desc = f"""create a new mailing list.

    /{prefix}create channel mychannel My Channel
    /{prefix}create group mygroup My Group
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

    groups, channels = [], []
    for mailinglist in get_client(bot).get_lists(advertised=True):
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
    prefix = get_default(bot, "command_prefix", "")
    text = f"Added, to leave send:\n/{prefix}leave_{payload}"
    _join(payload, message.get_sender_contact().addr, bot, message, replies, text)


def add_member_cmd(
    bot: DeltaBot, payload: str, message: Message, replies: Replies
) -> None:
    """add the given address to the given super group or channel."""
    mlid, addr = payload.split(maxsplit=1)
    _join(mlid, addr, bot, message, replies, f"{addr} added as member")


def _join(
    mlid: str,
    addr: str,
    bot: DeltaBot,
    message: Message,
    replies: Replies,
    success_msg: str,
) -> bool:
    try:
        mlist = get_client(bot).get_list(mlid)
        mlist.subscribe(
            addr, pre_verified=True, pre_confirmed=True, send_welcome_message=True
        )
        if success_msg:
            replies.add(text=success_msg, quote=message)
        return True
    except HTTPError as ex:
        bot.logger.exception(ex)
        replies.add(text="❌ Invalid ID", quote=message)
        return False


def leave_cmd(bot: DeltaBot, payload: str, message: Message, replies: Replies) -> None:
    """leave the given super group or channel."""
    _leave(payload, message.get_sender_contact().addr, bot, message, replies)


def remove_member_cmd(
    bot: DeltaBot, payload: str, message: Message, replies: Replies
) -> None:
    """remove the given address from the given super group or channel."""
    mlid, addr = payload.split(maxsplit=1)
    _leave(mlid, addr, bot, message, replies)


def _leave(
    mlid: str, addr: str, bot: DeltaBot, message: Message, replies: Replies
) -> None:
    try:
        mlist = get_client(bot).get_list(mlid)
        mlist.unsubscribe(addr)
    except ValueError as ex:
        bot.logger.exception(ex)
        replies.add(text="❌ You are not a member of that group/channel", quote=message)
    except HTTPError as ex:
        bot.logger.exception(ex)
        replies.add(text="❌ Invalid ID", quote=message)


def roles_cmd(bot: DeltaBot, payload: str, message: Message, replies: Replies) -> None:
    """get the addresses with administrative roles in the given super group or channel."""
    try:
        mlist = get_client(bot).get_list(payload)
        owners = []
        for owner in mlist.owners:
            owners.append(str(owner.address))
        moderators = []
        for moderator in mlist.moderators:
            moderators.append(str(moderator.address))
        text = ""
        if owners:
            text += "Owners:\n"
            for owner in owners:
                text += f"* {owner}\n"
        if moderators:
            text += "\nModerators:\n"
            for moderator in moderators:
                text += f"* {moderator}\n"
        replies.add(text=text or "❌ Empty List", quote=message)
    except Exception as ex:
        bot.logger.exception(ex)
        replies.add(text=f"❌ Error: {ex}", quote=message)


def create_cmd(bot: DeltaBot, payload: str, message: Message, replies: Replies) -> None:
    try:
        mltype, mladdr, mlname = payload.split(maxsplit=2)
        domain = get_client(bot).get_domain(get_default(bot, "domain", ""))
        if mltype == "channel":
            mltype = "legacy-announce"
        elif mltype == "group":
            mltype = "legacy-default"
        mlist = domain.create_list(mladdr, style_name=mltype)
        settings = mlist.settings
        settings["display_name"] = mlname
        settings["description"] = mlname
        settings.save()
        replies.add(text="Mailing list created successfully", quote=message)
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
        mlist = get_client(bot).get_list(mlid)
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


def add_owner_cmd(
    bot: DeltaBot, payload: str, message: Message, replies: Replies
) -> None:
    """add the given address as owner of the given mailing list."""
    try:
        mlid, addr = payload.split(maxsplit=1)
        mlist = get_client(bot).get_list(mlid)
        mlist.add_owner(addr)
        replies.add(text=f"{addr} added as owner", quote=message)
    except Exception as ex:
        bot.logger.exception(ex)
        replies.add(text=f"❌ Error: {ex}", quote=message)


def remove_owner_cmd(
    bot: DeltaBot, payload: str, message: Message, replies: Replies
) -> None:
    """remove the owner role of the given address in the given mailing list."""
    try:
        mlid, addr = payload.split(maxsplit=1)
        mlist = get_client(bot).get_list(mlid)
        mlist.remove_owner(addr)
        replies.add(text=f"{addr} removed from owners", quote=message)
    except Exception as ex:
        bot.logger.exception(ex)
        replies.add(text=f"❌ Error: {ex}", quote=message)


def add_moderator_cmd(
    bot: DeltaBot, payload: str, message: Message, replies: Replies
) -> None:
    """add the given address as moderator of the given mailing list."""
    try:
        mlid, addr = payload.split(maxsplit=1)
        mlist = get_client(bot).get_list(mlid)
        mlist.add_moderator(addr)
        replies.add(text=f"{addr} added as moderator", quote=message)
    except Exception as ex:
        bot.logger.exception(ex)
        replies.add(text=f"❌ Error: {ex}", quote=message)


def remove_moderator_cmd(
    bot: DeltaBot, payload: str, message: Message, replies: Replies
) -> None:
    """remove the moderator role of the given address in the given mailing list."""
    try:
        mlid, addr = payload.split(maxsplit=1)
        mlist = get_client(bot).get_list(mlid)
        mlist.remove_moderator(addr)
        replies.add(text=f"{addr} removed from moderators", quote=message)
    except Exception as ex:
        bot.logger.exception(ex)
        replies.add(text=f"❌ Error: {ex}", quote=message)


def link_cmd(bot: DeltaBot, payload: str, message: Message, replies: Replies) -> None:
    """link the the given channel with the given super group.

    All messages published in the channel will be sent also in the super group.
    """
    try:
        chanid, groupid = payload.split()
        chan_addr = get_client(bot).get_list(chanid).fqdn_listname
        group = get_client(bot).get_list(groupid)
        settings = group.settings
        if chan_addr not in settings["accept_these_nonmembers"]:
            settings["accept_these_nonmembers"].append(chan_addr)
        if chan_addr not in settings["acceptable_aliases"]:
            settings["acceptable_aliases"].append(chan_addr)
        settings.save()
        _join(
            chanid,
            group.fqdn_listname,
            bot,
            message,
            replies,
            f"Linked: {chanid} ➡️ {groupid}",
        )
    except Exception as ex:
        bot.logger.exception(ex)
        replies.add(text=f"❌ Error: {ex}", quote=message)


def unlink_cmd(bot: DeltaBot, payload: str, message: Message, replies: Replies) -> None:
    """unlink the the given channel and super group."""
    try:
        chanid, groupid = payload.split()
        chan_addr = get_client(bot).get_list(chanid).fqdn_listname
        group = get_client(bot).get_list(groupid)
        _leave(
            chanid,
            group.fqdn_listname,
            bot,
            message,
            replies,
        )
        settings = group.settings
        if chan_addr in settings["accept_these_nonmembers"]:
            settings["accept_these_nonmembers"].remove(chan_addr)
        if chan_addr in settings["acceptable_aliases"]:
            settings["acceptable_aliases"].remove(chan_addr)
        settings.save()
    except Exception as ex:
        bot.logger.exception(ex)
        replies.add(text=f"❌ Error: {ex}", quote=message)


def name_cmd(bot: DeltaBot, payload: str, message: Message, replies: Replies) -> None:
    """set the name of the given super group or channel."""
    try:
        mlid, name = payload.split(maxsplit=1)
        mlist = get_client(bot).get_list(mlid)
        addr = message.get_sender_contact().addr
        if bot.is_admin(addr) or mlist.is_owner_or_mod(addr):
            settings = mlist.settings
            settings["description"] = name
            settings["display_name"] = name
            settings.save()
            replies.add(text="Name updated", quote=message)
        else:
            replies.add(
                text="❌ You don't have enough permissions to perform that action",
                quote=message,
            )
    except Exception as ex:
        bot.logger.exception(ex)
        replies.add(text=f"❌ Error: {ex}", quote=message)


def topic_cmd(bot: DeltaBot, payload: str, message: Message, replies: Replies) -> None:
    """set the topic/description of the given super group or channel."""
    try:
        mlid, topic = payload.split(maxsplit=1)
        mlist = get_client(bot).get_list(mlid)
        addr = message.get_sender_contact().addr
        if bot.is_admin(addr) or mlist.is_owner_or_mod(addr):
            settings = mlist.settings
            settings["info"] = topic
            settings.save()
            replies.add(text="Topic updated", quote=message)
        else:
            replies.add(
                text="❌ You don't have enough permissions to perform that action",
                quote=message,
            )
    except Exception as ex:
        bot.logger.exception(ex)
        replies.add(text=f"❌ Error: {ex}", quote=message)


def listban_cmd(
    bot: DeltaBot, payload: str, message: Message, replies: Replies
) -> None:
    """ban the given address from the given super group or channel."""
    try:
        mlid, addr = payload.split(maxsplit=1)
        mlist = get_client(bot).get_list(mlid)
        sender = message.get_sender_contact().addr
        if bot.is_admin(sender) or mlist.is_owner_or_mod(sender):
            mlist.bans.add(addr)
            replies.add(text=f"{addr} banned", quote=message)
        else:
            replies.add(
                text="❌ You don't have enough permissions to perform that action",
                quote=message,
            )
    except Exception as ex:
        bot.logger.exception(ex)
        replies.add(text=f"❌ Error: {ex}", quote=message)


def listunban_cmd(
    bot: DeltaBot, payload: str, message: Message, replies: Replies
) -> None:
    """unban the given address from the given super group or channel."""
    try:
        mlid, addr = payload.split(maxsplit=1)
        mlist = get_client(bot).get_list(mlid)
        sender = message.get_sender_contact().addr
        if bot.is_admin(sender) or mlist.is_owner_or_mod(sender):
            mlist.bans.remove(addr)
            replies.add(text=f"{addr} unbanned", quote=message)
        else:
            replies.add(
                text="❌ You don't have enough permissions to perform that action",
                quote=message,
            )
    except Exception as ex:
        bot.logger.exception(ex)
        replies.add(text=f"❌ Error: {ex}", quote=message)


def siteban_cmd(
    bot: DeltaBot, payload: str, message: Message, replies: Replies
) -> None:
    """ban the given address from all mailing list."""
    try:
        get_client(bot).bans.add(payload)
        replies.add(text=f"{payload} banned", quote=message)
    except Exception as ex:
        bot.logger.exception(ex)
        replies.add(text=f"❌ Error: {ex}", quote=message)


def siteunban_cmd(
    bot: DeltaBot, payload: str, message: Message, replies: Replies
) -> None:
    """unban the given address from all mailing list."""
    try:
        get_client(bot).bans.remove(payload)
        replies.add(text=f"{payload} unbanned", quote=message)
    except Exception as ex:
        bot.logger.exception(ex)
        replies.add(text=f"❌ Error: {ex}", quote=message)
