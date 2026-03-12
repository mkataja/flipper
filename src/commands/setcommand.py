from collections.abc import Callable
from typing import Any, TypedDict

from commands.command import Command
from lib import geocoding
from models.user import User


class SettingResult(TypedDict):
    success: bool
    response: str


def setting_result(success: bool, response: str) -> SettingResult:
    return {"success": success, "response": response}


SettingHandler = Callable[[Command, Any, str], SettingResult]


BOOL_ALIASES: dict[str, bool] = {
    "true": True,
    "false": False,
    "on": True,
    "off": False,
    "yes": True,
    "no": False,
    "päälle": True,
    "pois": False,
    "kyllä": True,
    "ei": False,
}


def parse_bool(value: str) -> bool | str:
    normalized = (value or "").strip().lower()
    result = BOOL_ALIASES.get(normalized)
    if result is None:
        raise ValueError("sallitut arvot ovat: " + "/".join(BOOL_ALIASES.keys()))
    return result


def handle_set_home(command: Command, message: Any, address: str) -> SettingResult:
    if not address:
        return setting_result(False, "koti-asetukselle pitää antaa paikka")

    coordinates = geocoding.geocode(address)
    if coordinates is None:
        return setting_result(False, f"sijaintia {address} ei ole olemassa")

    user = User.get_or_create(message.sender)
    user.set_location(coordinates.latitude, coordinates.longitude)
    return setting_result(True, "uusi kotisijainti asetettu")


def handle_set_emoji(command: Command, message: Any, raw_value: str) -> SettingResult:
    try:
        enabled = parse_bool(raw_value)
    except ValueError as e:
        return setting_result(False, str(e))

    user = User.get_or_create(message.sender)
    user.set_emoji_enabled(enabled)
    state = "käytössä" if enabled else "pois käytöstä"
    return setting_result(True, f"emojit {state}")


SETTINGS: dict[str, SettingHandler] = {
    "koti": handle_set_home,
    "emoji": handle_set_emoji,
}


class SetCommand(Command):
    helpstr = "Käyttö: !set <asetus> <arvo>"

    def handle(self, message: Any) -> None:
        params = message.params.strip()
        if getattr(message, "commandword", None) == "koti":
            result = handle_set_home(self, message, params)
            self._reply_result(message, result)
            return

        if not params:
            self.replytoinvalidparams(message)
            return

        parts = params.split(maxsplit=1)
        setting_name = parts[0].lower()
        setting_value = parts[1].strip() if len(parts) > 1 else ""

        handler = SETTINGS.get(setting_name)
        if handler:
            result = handler(self, message, setting_value)
            self._reply_result(message, result)
            return

        self.replytoinvalidparams(
            message, f"Tuntematon asetus '{setting_name}'")

    def _reply_result(self, message: Any, result: SettingResult) -> None:
        if not result:
            self.replytoinvalidparams(message)
            return
        if result["success"]:
            message.reply_to(f"Ok, {result['response']}")
        else:
            message.reply_to(f"Virhe: {result['response']}")
