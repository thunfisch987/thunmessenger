from typing import Any

from kivy.core.clipboard import Clipboard
from kivy.properties import StringProperty
from kivymd.uix.list import (
    OneLineAvatarIconListItem,
    OneLineIconListItem,
    TwoLineListItem,
)


class InformationItem(OneLineIconListItem):
    divider = None
    icon_chooser = StringProperty("")

    def __init__(self, icon: str = "", **kwargs: Any):
        super().__init__(**kwargs)
        self.icon_chooser = icon

    def copy_to_clipboard(self) -> None:
        Clipboard.copy(self.text)


class SoundItem(OneLineAvatarIconListItem):
    divider = None


class MessageItem(TwoLineListItem):
    def __init__(self, text: str, sec: str, halign: str = "left") -> None:
        super().__init__(text=text, secondary_text=sec)
        self.ids["_lbl_primary"].halign = halign
        self.ids["_lbl_secondary"].halign = halign
