import unittest
from mfrc522.SimpleMFRC522 import SimpleMFRC522

HID = '61626364'
UID = [97, 98, 99, 100, 4]

class TestSimpleMFRC522(unittest.TestCase):
    def test_uid_to_hex(self):
        self.assertEqual(HID, SimpleMFRC522.uid_to_hex(UID))

    def test_hex_to_uid(self):
        self.assertEqual(UID, SimpleMFRC522.hex_to_uid(HID))
