import ipaddress
import json
import os
import socket as st
import sys
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from socket import AF_INET, SOCK_DGRAM, socket
from threading import Thread
from typing import Any

from Crypto.PublicKey import RSA
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.audio import Sound, SoundLoader
from kivy.core.window import Keyboard, Window
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.resources import resource_add_path
from kivy.uix.widget import Widget
from kivy.utils import escape_markup
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineAvatarIconListItem, TwoLineListItem
from kivymd.uix.list.list import CheckboxLeftWidget
from kivymd.uix.textfield import MDTextField

sound: Sound | None = None
sound_name: str | None

ip_set: set[str] = set()


class OKButton(MDRaisedButton):
    pass


class MessengerSocket(socket):
    def __init__(self) -> None:
        super(MessengerSocket, self).__init__(AF_INET, SOCK_DGRAM)
        return


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


@dataclass
class Sendable:
    def __dict_to_string(self) -> str:
        return json.dumps(self.__dict__)

    def __string_to_dict(self, json_msg: bytes) -> dict[str, str]:
        return json.loads(self.__decoded(json_msg))

    @staticmethod
    def __decoded(json_msg: bytes) -> str:
        return json_msg.decode("utf-8")

    def encoded(self) -> bytes:
        return self.__dict_to_string().encode("utf-8")

    def updt(self, json_msg: bytes) -> None:
        self.__dict__.update(self.__string_to_dict(json_msg))
        return


@dataclass
class Message(Sendable):
    name: str = ""
    msg: str = ""


class MessageItem(TwoLineListItem):
    def __init__(self, text: str, sec: str, halign: str = "left") -> None:
        super().__init__(text=text, secondary_text=sec)
        self.ids._lbl_primary.halign = halign
        self.ids._lbl_secondary.halign = halign


class Item(OneLineAvatarIconListItem):
    divider = None

    def set_icon(self, instance_check: CheckboxLeftWidget) -> None:
        global sound_name
        instance_check.active = True
        check_list: list[Widget] = instance_check.get_widgets(instance_check.group)
        for check in check_list:
            if check != instance_check:
                check.active = False
        sound_name = self.text


class MessageInput(MDTextField):
    ip_set_for_widget = ObjectProperty(ip_set)  # giving the kv file the list
    receiver: str
    item: MessageItem
    name: str
    message: Message
    incoming_message: Message

    def check_disabled(self, *args: Any, **kwargs: Any):
        return (
            self.ip_input.text if self.ip_input.text != "" else "127.0.0.1"
        ) not in ip_set

    def keyboard_on_key_down(
        self,
        window: Keyboard,
        keycode: tuple[int, str],
        text: str,
        modifiers: list[str],
    ) -> bool | None:
        if keycode[1] in ["enter", "return"]:
            self.send_message()
            return
        return super().keyboard_on_key_down(window, keycode, text, modifiers)

    def insert_msg(
        self, title: str, message: str, i_o: str, *args: Any, **kwargs: Any
    ) -> None:
        if i_o == "incoming":
            self.item = MessageItem(title, message, "left")
        elif i_o == "outgoing":
            self.item = MessageItem(title, message, "right")
        self.output.add_widget(self.item)
        self.scroll_view.scroll_to(self.item)
        return

    def send_message(self) -> None:
        if not self.ip_input.error and self.ip_input.text != "":
            self.receiver: str = self.ip_input.text
        else:
            self.receiver: str = "127.0.0.1"
        if self.receiver in ip_set:
            if self.text == "":
                return
            self.name: str = self.username.text[:9]
            self.message = Message(name=self.name, msg=self.text[:1000])
            esc_time: str = escape_markup(f"[{datetime.now().strftime('%H:%M')}] ")
            """returns the current time as '[HH:MM] ' """

            serversocket.sendto(self.message.encoded(), (self.receiver, 15200))
            if not self.name:
                self.insert_msg(f"{esc_time} You:", self.text, "outgoing")
            else:
                self.insert_msg(
                    f"{esc_time} {self.name} (You):",
                    self.text,
                    "outgoing",
                )
            if sound:
                sound.play()
        else:
            with open("pubkey.pem", "rb") as f:
                with socket() as send_key_socket:
                    send_key_socket.bind(("", 15202))
                    send_key_socket.connect((self.receiver, 15201))
                    send_key_socket.sendfile(f, 0)
            self.disabled = False
        self.text = ""
        self.focus = True
        self.error = False
        ip_set.add(self.receiver)
        return

    @staticmethod
    def listen_for_key() -> None:
        with socket() as key_socket:
            key_socket.bind(("", 15201))
            key_socket.listen(1)
            while True:
                sc, address = key_socket.accept()
                while data := sc.recv(1024):
                    print(data)
                    with open(f"pub-keys/{address[0]}.pem", "wb") as keyfile:
                        keyfile.write(data)

    def listen_for_msg(self) -> None:
        while True:
            json_data, address = serversocket.recvfrom(1024)
            if sound:
                sound.play()
            self.incoming_message = Message()
            self.incoming_message.updt(json_data)
            current_time = datetime.now().strftime("%H:%M")
            curry_time = f"[{current_time}] "
            esc_time = escape_markup(curry_time)
            if self.incoming_message.name != "":
                msg_title = esc_time + self.incoming_message.name
                if address[0] == "127.0.0.1":
                    Clock.schedule_once(
                        partial(
                            self.insert_msg,
                            f"{msg_title} (You):",
                            self.incoming_message.msg,
                            "incoming",
                        )
                    )

                else:
                    Clock.schedule_once(
                        partial(
                            self.insert_msg,
                            f"{msg_title}:",
                            self.incoming_message.msg,
                            "incoming",
                        )
                    )

            elif address[0] == "127.0.0.1":
                msg_title = esc_time + address[0]
                Clock.schedule_once(
                    partial(
                        self.insert_msg,
                        f"{msg_title} (You):",
                        self.incoming_message.msg,
                        "incoming",
                    )
                )

            else:
                msg_title = esc_time + address[0]
                Clock.schedule_once(
                    partial(
                        self.insert_msg,
                        f"{msg_title}:",
                        self.incoming_message.msg,
                        "incoming",
                    )
                )

    def on_parent(self, *args: Any, **kwargs: Any) -> None:
        receivethread = Thread(target=self.listen_for_msg, daemon=True)
        receivethread.start()
        keyrcvthread = Thread(target=self.listen_for_key, daemon=True)
        keyrcvthread.start()


class MessengerWindow(MDApp):
    dialog = None
    title = "Messenger"

    def __init__(self, **kwargs: Any) -> None:
        Window.softinput_mode = "below_target"  # type: ignore
        Config.set("input", "mouse", "mouse,multitouch_on_demand")
        conf = Config.set("input", "mouse", "mouse,multitouch_on_demand")
        print(f"\n\n\n{conf}\n\n\n")
        super().__init__(**kwargs)
        self.theme_cls.primary_palette = "Green"

    def build(self) -> None:
        self.theme_cls.theme_style = "Dark"
        self.icon = ""
        return Builder.load_file("./messengerMD.kv")

    def change_sound(self) -> None:
        global sound, sound_name
        try:
            sound_name
        except NameError:
            sound_name = ""
        if sound_name == "no sound":
            sound = None
        else:
            sound = SoundLoader.load(f"sounds/{sound_name}")
        self.dialog.dismiss()  # type:ignore

    def show_confirmation_dialog(self) -> None:
        if not self.dialog:
            self.dialog = MDDialog(
                title="Choose sound:",
                type="confirmation",
                items=[
                    Item(text="no sound"),
                    Item(text="bakugo.mp3"),
                    Item(text="jamie.mp3"),
                    Item(text="peekaboo.mp3"),
                    Item(text="sound.wav"),
                    Item(text="tequila.mp3"),
                ],
                buttons=[OKButton(text="OK")],
            )
        self.dialog.open()


if __name__ == "__main__":
    if hasattr(sys, "_MEIPASS"):
        resource_add_path(os.path.join(sys._MEIPASS))  # type: ignore
    try:
        os.mkdir("pubkeys")
    except OSError:
        pass
    else:
        print("folder created")
    serversocket = MessengerSocket()
    serversocket.bind(("", 15200))

    own_ip = st.gethostbyname(st.gethostname())
    if (not os.path.exists("mykey.pem") and not os.path.exists("pubkey.pem")) or (
        not os.path.exists("mykey.pem") or not os.path.exists("pubkey.pem")
    ):
        rsakey = RSA.generate(2048)
        with open("mykey.pem", "wb") as privfile:
            privfile.write(rsakey.export_key("PEM"))
        with open("pubkey.pem", "wb") as pubfile:
            pubfile.write(rsakey.public_key().export_key("PEM"))
    MessengerWindow().run()
else:
    print("imports not allowed")
