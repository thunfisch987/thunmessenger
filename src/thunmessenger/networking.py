__all__ = ("AES_Cipher_Message", "Message", "PublicKeyMessage", "MessengerSocket")

import json
from dataclasses import dataclass
from socket import AF_INET, SOCK_DGRAM, socket


@dataclass
class AES_Cipher_Message:
    nonce: str | bytes
    tag: str | bytes
    ciphertext: str | bytes


@dataclass
class Message:
    name: str = ""
    msg: str = ""

    def __dict_to_string(self) -> str:
        return json.dumps(self.__dict__)

    def __string_to_dict(self, json_msg: bytes) -> dict[str, str]:
        return json.loads(self.__decoded(json_msg))

    @staticmethod
    def __decoded(json_msg: bytes) -> str:
        return json_msg.decode("utf-8")

    def encoded(self) -> bytes:
        return self.__dict_to_string().encode("utf-8")

    def update_dict(self, json_msg: bytes) -> None:
        self.__dict__.update(self.__string_to_dict(json_msg))

    def encrypt(self):
        ...


class PublicKeyMessage:
    ...


class MessengerSocket(socket):
    def __init__(self) -> None:
        super(MessengerSocket, self).__init__(AF_INET, SOCK_DGRAM)
        return
