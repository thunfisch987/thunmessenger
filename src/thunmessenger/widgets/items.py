from typing import Any

from kivymd.uix.list import (
    OneLineIconListItem,
    OneLineAvatarIconListItem,
    CheckboxLeftWidget,
    TwoLineListItem,
)
from kivy.properties import StringProperty
from kivy.core.clipboard import Clipboard
from kivy.uix.widget import Widget


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

    def set_icon(self, instance_check: CheckboxLeftWidget) -> None:
        global sound_name
        instance_check.active = True
        check_list: list[Widget] = instance_check.get_widgets(instance_check.group)
        for check in check_list:
            if check != instance_check:
                check.active = False
        sound_name = self.text


class MessageItem(TwoLineListItem):
    def __init__(self, text: str, sec: str, halign: str = "left") -> None:
        super().__init__(text=text, secondary_text=sec)
        self.ids["_lbl_primary"].halign = halign
        self.ids["_lbl_secondary"].halign = halign
