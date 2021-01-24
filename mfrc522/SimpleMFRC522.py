# Code by Simon Monk https://github.com/simonmonk/

from . import MFRC522


class SimpleMFRC522:
    KEY = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    BLOCK_ADDRS = [8, 9, 10]

    def __init__(self, key=None):
        self.READER = MFRC522()

        if key is not None:
            self.KEY = key

    def read(self):
        while True:
            uid, text = self.read_no_block()
            if uid:
                break
        return uid, text

    def read_id(self):
        while True:
            uid = self.read_id_no_block()
            if uid:
                break
        return uid

    def read_id_no_block(self):
        (status, TagType) = self.READER.MFRC522_Request(self.READER.PICC_REQIDL)
        if status != self.READER.MI_OK:
            return None
        (status, uid) = self.READER.MFRC522_Anticoll()
        if status != self.READER.MI_OK:
            return None
        return self.uid_to_hex(uid)

    def read_no_block(self):
        (status, TagType) = self.READER.MFRC522_Request(self.READER.PICC_REQIDL)
        if status != self.READER.MI_OK:
            return None, None
        (status, uid) = self.READER.MFRC522_Anticoll()
        if status != self.READER.MI_OK:
            return None, None
        self.READER.MFRC522_SelectTag(uid)
        status = self.READER.MFRC522_Auth(self.READER.PICC_AUTHENT1A, 11, self.KEY, uid)
        data = []
        text_read = ""
        if status == self.READER.MI_OK:
            for block_num in self.BLOCK_ADDRS:
                block = self.READER.MFRC522_Read(block_num)
                if block:
                    data += block
            if data:
                text_read = "".join(chr(i) for i in data)
        self.READER.MFRC522_StopCrypto1()
        return self.uid_to_hex(uid), text_read

    def write(self, text):
        while True:
            uid, text_in = self.write_no_block(text)
            if uid:
                break
        return uid, text_in

    def write_no_block(self, text):
        (status, TagType) = self.READER.MFRC522_Request(self.READER.PICC_REQIDL)
        if status != self.READER.MI_OK:
            return None, None
        (status, uid) = self.READER.MFRC522_Anticoll()
        if status != self.READER.MI_OK:
            return None, None
        self.READER.MFRC522_SelectTag(uid)
        status = self.READER.MFRC522_Auth(self.READER.PICC_AUTHENT1A, 11, self.KEY, uid)
        self.READER.MFRC522_Read(11)
        if status == self.READER.MI_OK:
            data = bytearray()
            data.extend(
                bytearray(text.ljust(len(self.BLOCK_ADDRS) * 16).encode("ascii"))
            )
            i = 0
            for block_num in self.BLOCK_ADDRS:
                self.READER.MFRC522_Write(block_num, data[(i * 16) : (i + 1) * 16])
                i += 1
        self.READER.MFRC522_StopCrypto1()
        return self.uid_to_hex(uid), text[0 : (len(self.BLOCK_ADDRS) * 16)]

    @staticmethod
    def uid_to_hex(uid):
        return bytes(uid[:4]).hex()
