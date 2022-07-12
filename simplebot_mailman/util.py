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
