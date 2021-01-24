from mfrc522.MFRC522 import MFRC522
import unittest

VALUE_BLOCK = b"\x05\x00\x00\x00\xfa\xff\xff\xff\x05\x00\x00\x00\x05\xfa\x05\xfa"


class TestMFRC522(unittest.TestCase):
    def test_format_value_block(self):
        self.assertEqual(
            MFRC522.format_value_block(5, 5),
            VALUE_BLOCK,
        )

    def test_check_value_block(self):
        self.assertTrue(MFRC522.check_value_block(VALUE_BLOCK))

    def test_self_format_then_check(self):
        self.assertTrue(MFRC522.check_value_block(MFRC522.format_value_block()))
