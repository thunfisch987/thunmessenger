from kivymd.uix.button import MDRaisedButton
from kivymd.uix.button.button import (
    OldButtonIconMixin,
    ButtonContentsIconText,
    ButtonElevationBehaviour,
    BaseButton,
)
from kivymd.uix.behaviors import FakeRectangularElevationBehavior


class RaisedIconButton(
    OldButtonIconMixin,
    FakeRectangularElevationBehavior,
    ButtonElevationBehaviour,
    ButtonContentsIconText,
    BaseButton,
):  # pyright: reportIncompatibleMethodOverride=false,reportIncompatibleVariableOverride=false
    _default_md_bg_color = None
    _default_md_bg_color_disabled = None
    _default_theme_text_color = "Custom"
    _default_text_color = "PrimaryHue"


class OKButton(MDRaisedButton):
    pass
