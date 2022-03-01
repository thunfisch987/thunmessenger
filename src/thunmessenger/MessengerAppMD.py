import ipaddress
import json
import os
import socket as st
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from socket import AF_INET, SOCK_DGRAM, socket
from threading import Thread
from typing import Any

from Crypto.PublicKey import RSA
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.utils import escape_markup
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineAvatarIconListItem, TwoLineListItem
from kivymd.uix.textfield import MDTextField

sound = None
soundname: str | None
ip_list: set[str] = set()


class OKButton(MDRaisedButton):
    pass


class MessengerSocket(socket):
    def __init__(self) -> None:
        super(MessengerSocket, self).__init__(AF_INET, SOCK_DGRAM)
        return


class IPInput(MDTextField):
    def on_focus(self, instance_text_field, focus) -> None:

        super().on_focus(instance_text_field, focus)
        if not focus:
            self.on_text_validate()
        return

    def on_text_validate(self, *args: Any, **kwargs: Any) -> None:
        super().on_text_validate(*args, **kwargs)
        if self.text != "":
            try:
                ipaddress.ip_address(self.text)
            except ValueError:
                self.error = True
        return


@dataclass
class Sendable:
    def __jsondumps(self) -> str:
        return json.dumps(self.__dict__)

    def __jsonloads(self, jsonmsg: bytes) -> dict[str, str]:
        return json.loads(self.__decoded(jsonmsg))

    def __decoded(self, jsonmsg: bytes) -> str:
        return jsonmsg.decode("utf-8")

    def encoded(self) -> bytes:
        return self.__jsondumps().encode("utf-8")

    def updt(self, jsonmsg: bytes) -> None:
        self.__dict__.update(self.__jsonloads(jsonmsg))
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

    def set_icon(self, instance_check) -> None:
        global soundname
        instance_check.active = True
        check_list: list = instance_check.get_widgets(instance_check.group)
        for check in check_list:
            if check != instance_check:
                check.active = False
        soundname = self.text


class MessageInput(MDTextField):
    output = ObjectProperty(None)
    username = ObjectProperty(None)
    ip_input = ObjectProperty(None)
    scroll_view = ObjectProperty(None)
    ip_list_for_widget = ObjectProperty(ip_list)  # giving the kv file the list

    def check_disabled(self, *args: Any, **kwargs):
        return (
            self.ip_input.text if self.ip_input.text != "" else "127.0.0.1"
        ) not in ip_list

    def keyboard_on_key_down(self, *args: Any, **kwargs: Any) -> None | bool:
        if args[1][1] in ["enter", "return"]:
            self.sendmessage()
            return
        return super().keyboard_on_key_down(*args, **kwargs)

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

    def sendmessage(self) -> None:
        if not self.ip_input.error and self.ip_input.text != "":
            self.empfaenger: str = self.ip_input.text
        else:
            self.empfaenger: str = "127.0.0.1"
        if self.empfaenger in ip_list:
            if self.text == "":
                return
            self.name: str = self.username.text
            self.message = Message(name=self.name, msg=self.text[:1000])
            current_time: str = datetime.now().strftime("%H:%M")
            curry_time = f"[{current_time}] "
            esc_time = escape_markup(curry_time)
            serversocket.sendto(self.message.encoded(), (self.empfaenger, 15200))
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
                with socket() as sendkeysocket:
                    sendkeysocket.bind(("", 15202))
                    sendkeysocket.connect((self.empfaenger, 15201))
                    sendkeysocket.sendfile(f, 0)
            self.disabled = False
        self.text = ""
        self.focus = True
        self.error = False
        ip_list.add(self.empfaenger)
        return

    def listenforkey(self) -> None:
        with socket() as keysocket:
            keysocket.bind(("", 15201))
            keysocket.listen(1)
            while True:
                sc, adress = keysocket.accept()
                while data := sc.recv(1024):
                    print(data)
                    with open(f"pubkeys/{adress[0]}.pem", "wb") as keyfile:
                        keyfile.write(data)

    def listenformsg(self) -> None:
        while True:
            jsondata, addr = serversocket.recvfrom(1024)
            if sound:
                sound.play()
            self.incmessage = Message()
            self.incmessage.updt(jsondata)
            current_time = datetime.now().strftime("%H:%M")
            curry_time = f"[{current_time}] "
            esc_time = escape_markup(curry_time)
            if self.incmessage.name != "":
                msgtitle = esc_time + self.incmessage.name
                if addr[0] == "127.0.0.1":
                    Clock.schedule_once(
                        partial(
                            self.insert_msg,
                            f"{msgtitle} (You):",
                            self.incmessage.msg,
                            "incoming",
                        )
                    )

                else:
                    Clock.schedule_once(
                        partial(
                            self.insert_msg,
                            f"{msgtitle}:",
                            self.incmessage.msg,
                            "incoming",
                        )
                    )

            elif addr[0] == "127.0.0.1":
                msgtitle = esc_time + addr[0]
                Clock.schedule_once(
                    partial(
                        self.insert_msg,
                        f"{msgtitle} (You):",
                        self.incmessage.msg,
                        "incoming",
                    )
                )

            else:
                msgtitle = esc_time + addr[0]
                Clock.schedule_once(
                    partial(
                        self.insert_msg,
                        f"{msgtitle}:",
                        self.incmessage.msg,
                        "incoming",
                    )
                )

    def on_parent(self, *args: Any, **kwargs: Any) -> None:
        receivethread = Thread(target=self.listenformsg, daemon=True)
        receivethread.start()
        keyrcvthread = Thread(target=self.listenforkey, daemon=True)
        keyrcvthread.start()


class MessengerWindow(MDApp):
    dialog = None
    title = "Messenger"

    def __init__(self, *args, **kwargs) -> None:
        Window.softinput_mode = "below_target"  # type: ignore
        Config.set("input", "mouse", "mouse,multitouch_on_demand")
        super().__init__(*args, **kwargs)
        self.theme_cls.primary_palette = "Green"

    def build(self):
        self.theme_cls.theme_style = "Dark"
        return Builder.load_file("./messengerMD.kv")

    def change_sound(self) -> None:
        global sound, soundname
        try:
            soundname
        except NameError:
            soundname = ""
        if soundname == "no sound":
            sound = None
        else:
            sound = SoundLoader.load(f"sounds/{soundname}")
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
    try:
        os.mkdir("pubkeys")
    except OSError as e:
        print(e)
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
