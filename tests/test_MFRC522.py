from mfrc522.MFRC522 import MFRC522
import unittest


class TestMFRC522(unittest.TestCase):
    def test_format_value_block(self):
        self.assertTrue(MFRC522.check_value_block(MFRC522.format_value_block()))
