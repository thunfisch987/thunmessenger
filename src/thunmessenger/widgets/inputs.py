from typing import Any
import ipaddress
from kivymd.uix.textfield import MDTextField


class IPInput(MDTextField):
    def on_focus(self, instance_text_field: MDTextField, focus: bool) -> None:

        super().on_focus(instance_text_field, focus)
        if not focus:
            self.on_text_validate()
        return

    def on_text_validate(self, *args: Any, **kwargs: Any) -> None:
        if self.text != "":
            try:
                ipaddress.ip_address(self.text)
            except ValueError:
                self.error = True
        return
