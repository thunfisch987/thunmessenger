__all__ = ("new_cipher", "create_rsa_files")

import os
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.PublicKey import RSA


def new_cipher():
    return AES.new(
        get_random_bytes(16), AES.MODE_EAX
    )  # pyright: reportUnknownMemberType=false


def create_rsa_files():
    if (not os.path.exists("mykey.pem") and not os.path.exists("pubkey.pem")) or (
        not os.path.exists("mykey.pem") or not os.path.exists("pubkey.pem")
    ):
        rsakey = RSA.generate(2048)
        with open("mykey.pem", "wb") as privfile:
            privfile.write(rsakey.export_key("PEM"))
        with open("pubkey.pem", "wb") as pubfile:
            pubfile.write(rsakey.public_key().export_key("PEM"))


if __name__ == "__main__":
    print("This is a module, not a script")
