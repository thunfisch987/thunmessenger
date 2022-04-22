import os
import socket as st
import sys
from datetime import datetime
from functools import partial
from socket import socket
from threading import Thread
from typing import Any

from encryption import create_rsa_files, new_cipher
from kivy_imports import (
    Builder,
    Clock,
    Config,
    Keyboard,
    ObjectProperty,
    ScrollView,
    Sound,
    SoundLoader,
    Widget,
    Window,
    escape_markup,
    resource_add_path,
)
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import CheckboxLeftWidget, MDList
from kivymd.uix.textfield import MDTextField
from networking import Message, MessengerSocket
from widgets import InformationItem, MessageItem, SoundItem

sound: Sound | None = None
sendkey_port = None
own_port = None
message_port = None


ip_set: set[str] = set()


class MessageInput(MDTextField):
    output = ObjectProperty(MDList)
    username = ObjectProperty(MDTextField)
    ip_input = ObjectProperty(MDTextField)
    scroll_view = ObjectProperty(ScrollView)
    ip_set_for_widget = ObjectProperty(ip_set)
    """giving the kv file the set of ip_adresses"""
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
        global sendkey_port
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

            serversocket.sendto(self.message.encoded(), (self.receiver, message_port))
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
                    send_key_socket.bind(("", 0))
                    sendkey_port = send_key_socket.getsockname()[1]
                    send_key_socket.connect((self.receiver, self.key_port))
                    send_key_socket.sendfile(f, 0)
            self.disabled = False
        self.text = ""
        self.focus = True
        self.error = False
        ip_set.add(self.receiver)
        return

    def listen_for_key(self) -> None:
        with socket() as key_socket:
            key_socket.bind(("", 0))
            self.key_port = key_socket.getsockname()[1]
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
            self.incoming_message.update_dict(json_data)
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
    confirmation_dialog = None
    information_dialog = None
    title = "Messenger"

    def __init__(self, **kwargs: Any) -> None:
        Window.softinput_mode = "below_target"  # type: ignore
        Config.set("input", "mouse", "mouse,multitouch_on_demand")
        super().__init__(**kwargs)
        self.theme_cls.primary_palette = "Green"

    def build(self) -> None:
        self.theme_cls.theme_style = "Dark"
        self.icon = ""
        return Builder.load_file("./messengerMD.kv")

    def change_sound_and_set_icon(
        self, instance_check: CheckboxLeftWidget, item: SoundItem
    ) -> None:
        global sound
        instance_check.active = True
        check_list: list[Widget] = instance_check.get_widgets(instance_check.group)
        for check in check_list:
            if check != instance_check:
                check.active = False
        sound_name = item.text
        if sound_name == "no sound":
            sound = None
            return
        sound = SoundLoader.load(f"sounds/{sound_name}")

    def show_information_dialog(self):
        if not self.information_dialog:
            self.information_dialog = MDDialog(
                title="Port & IP Address",
                type="simple",
                items=[
                    InformationItem(text=own_ip, icon="map-marker"),
                    InformationItem(text=str(message_port), icon="ethernet"),
                ],
            )
        self.information_dialog.open()

    def show_confirmation_dialog(self) -> None:
        if not self.confirmation_dialog:
            self.confirmation_dialog = MDDialog(
                title="Choose sound:",
                type="simple",
                items=[
                    SoundItem(text="no sound"),
                    SoundItem(text="bakugo.mp3"),
                    SoundItem(text="jamie.mp3"),
                    SoundItem(text="peekaboo.mp3"),
                    SoundItem(text="sound.wav"),
                    SoundItem(text="tequila.mp3"),
                ],
            )
        self.confirmation_dialog.open()


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
    serversocket.bind(("", 0))
    message_port = serversocket.getsockname()[1]

    own_ip = st.gethostbyname(st.gethostname())
    create_rsa_files()
    new_aes = new_cipher()
    MessengerWindow().run()
else:
    print("imports not allowed")
