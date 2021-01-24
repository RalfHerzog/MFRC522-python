# Adapted from code by Simon Monk https://github.com/simonmonk/

from . import MFRC522


class SimpleMFRC522:
    KEY = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    BLOCK_ADDRS = [8, 9, 10]

    def __init__(self, key=None):
        self.reader = MFRC522()

        if key is not None:
            self.KEY = key

    def read(self):
        while True:
            hid, text = self.read_no_block()
            if hid:
                break
        return hid, text

    def read_id(self):
        while True:
            hid = self.read_id_no_block()
            if hid:
                break
        return hid

    def read_id_no_block(self):
        (status, TagType) = self.reader.MFRC522_Request(self.reader.PICC_REQIDL)
        if status != self.reader.MI_OK:
            return None
        (status, uid) = self.reader.MFRC522_Anticoll()
        if status != self.reader.MI_OK:
            return None
        return self.uid_to_hex(uid)

    def read_no_block(self):
        (status, TagType) = self.reader.MFRC522_Request(self.reader.PICC_REQIDL)
        if status != self.reader.MI_OK:
            return None, None
        (status, uid) = self.reader.MFRC522_Anticoll()
        if status != self.reader.MI_OK:
            return None, None
        self.reader.MFRC522_SelectTag(uid)
        status = self.reader.MFRC522_Auth(self.reader.PICC_AUTHENT1A, 11, self.KEY, uid)
        data = []
        text_read = ""
        if status == self.reader.MI_OK:
            for block_num in self.BLOCK_ADDRS:
                block = self.reader.MFRC522_Read(block_num)
                if block:
                    data += block
            if data:
                text_read = bytes(data).decode()
        self.reader.MFRC522_StopCrypto1()
        return self.uid_to_hex(uid), text_read

    def write(self, text):
        while True:
            hid, text_in = self.write_no_block(text)
            if hid:
                break
        return hid, text_in

    def write_no_block(self, text):
        (status, TagType) = self.reader.MFRC522_Request(self.reader.PICC_REQIDL)
        if status != self.reader.MI_OK:
            return None, None
        (status, uid) = self.reader.MFRC522_Anticoll()
        if status != self.reader.MI_OK:
            return None, None
        self.reader.MFRC522_SelectTag(uid)
        status = self.reader.MFRC522_Auth(self.reader.PICC_AUTHENT1A, 11, self.KEY, uid)
        if status == self.reader.MI_OK:
            data = bytearray(text.ljust(len(self.BLOCK_ADDRS) * 16).encode())
            for i, block_num in enumerate(self.BLOCK_ADDRS):
                self.reader.MFRC522_Write(block_num, data[(i * 16): (i + 1) * 16])
        self.reader.MFRC522_StopCrypto1()
        return self.uid_to_hex(uid), text[0 : (len(self.BLOCK_ADDRS) * 16)]

    @staticmethod
    def uid_to_hex(uid):
        return bytes(uid[:4]).hex()
