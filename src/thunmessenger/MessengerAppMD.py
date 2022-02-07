from dataclasses import dataclass
from datetime import datetime
import ipaddress
import json
import re
import socket as st
from threading import Thread

from kivy.lang import Builder
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
from kivy.utils import escape_markup

from kivymd.app import MDApp
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineAvatarIconListItem
from kivymd.uix.list import TwoLineListItem
from kivymd.uix.button import MDRaisedButton
from kivy.core.audio import SoundLoader
from kivy.properties import ObjectProperty

sound = None


class MessengerSocket(st.socket):
    def __init__(self, family: st.AddressFamily = st.AF_INET, type: st.SocketKind = st.SOCK_DGRAM) -> None:
        super(MessengerSocket, self).__init__(family, type)
        return


class IPInput(MDTextField):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def on_focus(self, instance, value) -> None:
        super().on_focus(instance, value)
        if not value:
            self.on_text_validate()
        return

    def on_text_validate(self, *args, **kwargs) -> None:
        super().on_text_validate(*args, **kwargs)
        if self.text != "":
            try:
                ipaddress.ip_address(self.text)
            except ValueError as e:
                self.error = True
        return


@dataclass
class Message:
    name: str = ""
    msg: str = ""

    def __jsondumps(self) -> str:
        return json.dumps(self.__dict__)

    def __jsonloads(self, jsonmsg: bytes) -> dict:
        return json.loads(self.__decoded(jsonmsg))

    def __decoded(self, jsonmsg: bytes) -> str:
        return jsonmsg.decode("utf-8")

    def encoded(self) -> bytes:
        return self.__jsondumps().encode("utf-8")

    def updt(self, jsonmsg: bytes) -> None:
        self.__dict__.update(self.__jsonloads(jsonmsg))
        return


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
        check_list = instance_check.get_widgets(instance_check.group)
        for check in check_list:
            if check != instance_check:
                check.active = False
        soundname = self.text


class MessageInput(MDTextField):
    output = ObjectProperty(None)
    username = ObjectProperty(None)
    ip_input = ObjectProperty(None)
    scroll_view = ObjectProperty(None)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def keyboard_on_key_down(self, *args, **kwargs) -> None | bool:
        if args[1][1] in ["enter", "return"]:
            self.sendmessage()
            return
        return super().keyboard_on_key_down(*args, **kwargs)

    def insert_msg(self, title: str, message: str, i_o: str) -> None:
        if i_o == "incoming":
            self.item = MessageItem(title, message, "left")
        elif i_o == "outgoing":
            self.item = MessageItem(title, message, "right")
        self.output.add_widget(self.item)
        self.scroll_view.scroll_to(self.item)
        return

    def sendmessage(self):
        global serversocket
        if self.text == "":
            return
        # Message
        self.name = self.username.text
        self.msg = self.text
        self.message = Message(name=self.name, msg=self.msg)
        if not self.ip_input.error:
            self.empfaenger = self.ip_input.text
        else:
            self.empfaenger = "localhost"
        serversocket.sendto(self.message.encoded(),
                            (self.empfaenger, 15200))
        if self.name == "":
            self.insert_msg("You", self.text, "outgoing")
        else:
            self.insert_msg(self.username.text, self.text, "incoming")
        if sound:
            sound.play()
        self.text = ""
        self.focus = True
        return

    def listenformsg(self):
        global serversocket
        while True:
            # print("-----running---------")
            jsondata, addr = serversocket.recvfrom(1024)
            if sound:
                sound.play()
            self.incmessage = Message()
            self.incmessage.updt(jsondata)
            # print("name:", self.incmessage.name)
            # print("msg:", self.incmessage.msg)
            current_time = datetime.now().strftime("%H:%M")
            curry_time = "[" + current_time + "] "
            esc_time = escape_markup(curry_time)
            if self.incmessage.name != "":
                msgtitle = esc_time + self.incmessage.name
                if addr[0] == "127.0.0.1":
                    self.insert_msg(msgtitle + " (You):",
                                    self.incmessage.msg,
                                    "incoming")
                    self.output.add_widget(MessageItem(
                        esc_time + self.incmessage.name + " (You):", self.incmessage.msg, halign="left"))
                else:
                    self.insert_msg(msgtitle + ":",
                                    self.incmessage.msg,
                                    "incoming")
                    self.output.add_widget(MessageItem(
                        esc_time + self.incmessage.name + ":", self.incmessage.msg, halign="left"))
            elif addr[0] == "127.0.0.1":
                msgtitle = esc_time + addr[0]
                self.insert_msg(msgtitle + " (You):",
                                self.incmessage.msg, "incoming")
            else:
                msgtitle = esc_time + addr[0]
                self.insert_msg(msgtitle + ":",
                                self.incmessage.msg, "incoming")

    def on_parent(self, *args, **kwargs) -> None:
        receivethread = Thread(target=self.listenformsg, daemon=True)
        receivethread.start()


class MessengerWindow(MDApp):
    dialog = None
    title = 'Messenger'

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.theme_cls.primary_palette = "Green"
        # self.startlistening()

    # def startlistening(self) -> None:
    #     receivethread = Thread(target=self.listenformsg, daemon=True)
    #     receivethread.start()

    def build(self):
        return Builder.load_file('./messengerMD.kv')

    def change_sound(self) -> None:
        global sound, soundname
        try:
            soundname
        except NameError:
            soundname = ""
        if soundname == "no sound":
            sound = None
        else:
            sound = SoundLoader.load("sounds/" + soundname)
        self.dialog.dismiss()

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
                buttons=[
                    MDRaisedButton(text="OK")
                ]
            )
        self.dialog.open()


if __name__ == '__main__':
    serversocket = MessengerSocket()
    serversocket.bind(("", 15200))
    MessengerWindow().run()
