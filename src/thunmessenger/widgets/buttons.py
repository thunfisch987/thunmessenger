# pyright: reportIncompatibleMethodOverride=false
# pyright: reportIncompatibleVariableOverride=false
from kivymd.uix.behaviors import FakeRectangularElevationBehavior
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.button.button import (
    BaseButton,
    ButtonContentsIconText,
    ButtonElevationBehaviour,
    OldButtonIconMixin,
)


class RaisedIconButton(
    OldButtonIconMixin,
    FakeRectangularElevationBehavior,
    ButtonElevationBehaviour,
    ButtonContentsIconText,
    BaseButton,
):
    _default_md_bg_color = None
    _default_md_bg_color_disabled = None
    _default_theme_text_color = "Custom"
    _default_text_color = "PrimaryHue"


class OKButton(MDRaisedButton):
    pass
