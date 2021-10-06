# Adapted from code by Simon Monk https://github.com/simonmonk/

from . import MFRC522
from .exceptions import MFRC522Exception


class SimpleMFRC522:
    def __init__(self, pin_rst, key=None, block_addresses=None):
        self.reader = MFRC522(pin_rst)

        self.key = key or [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
        # self.block_addresses = block_addresses or [8, 9, 10]
        self.block_addresses = block_addresses

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.reader.close_mfrc522()

    def read(self):
        while True:
            hid, text = self.read_no_block()
            if hid:
                return hid, text

    def read_id(self):
        while True:
            hid = self.read_id_no_block()
            if hid:
                return hid

    def read_id_no_block(self):
        status, tag_type = self.reader.mfrc522_request(self.reader.PICC_REQIDL)
        if status != self.reader.MI_OK:
            return None
        status, uid = self.reader.mfrc522_anticoll()
        if status != self.reader.MI_OK:
            return None
        return self.uid_to_hex(uid)

    def read_no_block(self):
        status, tag_type = self.reader.mfrc522_request(self.reader.PICC_REQIDL)
        if status != self.reader.MI_OK:
            return None, None
        status, uid = self.reader.mfrc522_anticoll()
        if status != self.reader.MI_OK:
            return None, None
        self.reader.mfrc522_select_tag(uid)
        status = self.reader.mfrc522_auth(self.reader.PICC_AUTHENT1A, 11, self.key, uid)
        data = []
        text_read = ""
        if status == self.reader.MI_OK and self.block_addresses is not None:
            for block_num in self.block_addresses:
                try:
                    data += self.reader.mfrc522_read(block_num)
                except MFRC522Exception:
                    pass
            if data:
                text_read = bytes(data).decode()
        self.reader.mfrc522_stop_crypto1()
        return self.uid_to_hex(uid), text_read

    def write(self, text):
        while True:
            hid, text_in = self.write_no_block(text)
            if hid:
                return hid, text_in

    def write_no_block(self, text):
        if self.block_addresses is None:
            raise MFRC522Exception("cannot write without block_addresses")
        status, tag_type = self.reader.mfrc522_request(self.reader.PICC_REQIDL)
        if status != self.reader.MI_OK:
            return None, None
        status, uid = self.reader.mfrc522_anticoll()
        if status != self.reader.MI_OK:
            return None, None
        self.reader.mfrc522_select_tag(uid)
        status = self.reader.mfrc522_auth(self.reader.PICC_AUTHENT1A, 11, self.key, uid)
        if status == self.reader.MI_OK:
            data = bytearray(text.ljust(len(self.block_addresses) * 16).encode())
            for i, block_num in enumerate(self.block_addresses):
                self.reader.mfrc522_write(block_num, data[(i * 16): (i + 1) * 16])
        self.reader.mfrc522_stop_crypto1()
        return self.uid_to_hex(uid), text[0: (len(self.block_addresses) * 16)]

    def dump_no_block(self):
        status, tag_type = self.reader.mfrc522_request(self.reader.PICC_REQIDL)
        if status != self.reader.MI_OK:
            return None, None
        status, uid = self.reader.mfrc522_anticoll()
        if status != self.reader.MI_OK:
            return None, None
        self.reader.mfrc522_select_tag(uid)
        data = self.reader.mfrc522_dump_classic1k([self.key] * 32, uid)
        self.reader.mfrc522_stop_crypto1()
        assert len(data) <= 1024
        return self.uid_to_hex(uid), data

    def dump(self):
        while True:
            hid, data = self.dump_no_block()
            if hid:
                return hid, data

    def close(self):
        self.reader.close_mfrc522()

    @staticmethod
    def uid_to_hex(uid):
        return bytes(uid[:4]).hex()

    @staticmethod
    def hex_to_uid(hid):
        data = list(bytes.fromhex(hid))
        data.append(MFRC522.calculate_bcc(data))
        return data
