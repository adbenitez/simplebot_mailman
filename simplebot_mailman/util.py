"""Utilities"""

from mailmanclient import Client
from simplebot.bot import DeltaBot


def get_default(bot: DeltaBot, key: str, value: str = None) -> str:
    scope = __name__.split(".", maxsplit=1)[0]
    val = bot.get(key, scope=scope)
    if val is None and value is not None:
        bot.set(key, value, scope=scope)
        val = value
    return val


def get_client(bot: DeltaBot) -> Client:
    return Client(
        get_default(bot, "api_url"),
        get_default(bot, "api_username"),
        get_default(bot, "api_password"),
    )


def get_address(bot: DeltaBot, client: Client, addr: str) -> str:
    default_domain = get_default(bot, "domain", "")
    if "@" in addr:
        user_id, domain = addr.split("@")
    else:
        user_id, domain = addr, default_domain
    if domain == default_domain:
        try:
            addr = client.get_user(user_id).addresses[0].email
        except Exception:
            pass
    return addr
