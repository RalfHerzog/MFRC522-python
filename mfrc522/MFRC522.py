#!/usr/bin/env python
# -*- coding: utf8 -*-
#
#    Copyright 2014,2018 Mario Gomez <mario.gomez@teubi.co>
#
#    This file is part of MFRC522-Python
#    MFRC522-Python is a simple Python implementation for
#    the MFRC522 NFC Card Reader for the Raspberry Pi.
#
#    MFRC522-Python is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    MFRC522-Python is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with MFRC522-Python.  If not, see <http://www.gnu.org/licenses/>.
#
import logging
from functools import reduce
from operator import xor

try:
    import RPi.GPIO as GPIO
    import spidev
except ImportError:
    import sys

    if sys.platform != "linux":
        import unittest.mock as mock

        GPIO = mock.Mock()
        spidev = mock.Mock()
    else:
        raise

from .exceptions import MFRC522Exception


class MFRC522:
    MAX_LEN = 16

    PCD_IDLE = 0x00
    PCD_AUTHENT = 0x0E
    PCD_RECEIVE = 0x08
    PCD_TRANSMIT = 0x04
    PCD_TRANSCEIVE = 0x0C
    PCD_RESETPHASE = 0x0F
    PCD_CALCCRC = 0x03

    PICC_REQIDL = 0x26
    PICC_REQALL = 0x52
    PICC_ANTICOLL = 0x93
    PICC_SElECTTAG = 0x93
    PICC_AUTHENT1A = 0x60
    PICC_AUTHENT1B = 0x61
    PICC_READ = 0x30
    PICC_WRITE = 0xA0
    PICC_DECREMENT = 0xC0
    PICC_INCREMENT = 0xC1
    PICC_RESTORE = 0xC2
    PICC_TRANSFER = 0xB0
    PICC_HALT = 0x50
    PICC_UNLOCK1 = 0x40
    PICC_UNLOCK2 = 0x43

    MI_OK = 0
    MI_NOTAGERR = 1
    MI_ERR = 2
    MI_TIMEOUT = 3

    Reserved00 = 0x00
    CommandReg = 0x01
    CommIEnReg = 0x02
    DivlEnReg = 0x03
    CommIrqReg = 0x04
    DivIrqReg = 0x05
    ErrorReg = 0x06
    Status1Reg = 0x07
    Status2Reg = 0x08
    FIFODataReg = 0x09
    FIFOLevelReg = 0x0A
    WaterLevelReg = 0x0B
    ControlReg = 0x0C
    BitFramingReg = 0x0D
    CollReg = 0x0E
    Reserved01 = 0x0F

    Reserved10 = 0x10
    ModeReg = 0x11
    TxModeReg = 0x12
    RxModeReg = 0x13
    TxControlReg = 0x14
    TxAutoReg = 0x15
    TxSelReg = 0x16
    RxSelReg = 0x17
    RxThresholdReg = 0x18
    DemodReg = 0x19
    Reserved11 = 0x1A
    Reserved12 = 0x1B
    MifareReg = 0x1C
    Reserved13 = 0x1D
    Reserved14 = 0x1E
    SerialSpeedReg = 0x1F

    Reserved20 = 0x20
    CRCResultRegM = 0x21
    CRCResultRegL = 0x22
    Reserved21 = 0x23
    ModWidthReg = 0x24
    Reserved22 = 0x25
    RFCfgReg = 0x26
    GsNReg = 0x27
    CWGsPReg = 0x28
    ModGsPReg = 0x29
    TModeReg = 0x2A
    TPrescalerReg = 0x2B
    TReloadRegH = 0x2C
    TReloadRegL = 0x2D
    TCounterValueRegH = 0x2E
    TCounterValueRegL = 0x2F

    Reserved30 = 0x30
    TestSel1Reg = 0x31
    TestSel2Reg = 0x32
    TestPinEnReg = 0x33
    TestPinValueReg = 0x34
    TestBusReg = 0x35
    AutoTestReg = 0x36
    VersionReg = 0x37
    AnalogTestReg = 0x38
    TestDAC1Reg = 0x39
    TestDAC2Reg = 0x3A
    TestADCReg = 0x3B
    Reserved31 = 0x3C
    Reserved32 = 0x3D
    Reserved33 = 0x3E
    Reserved34 = 0x3F

    serNum = []

    def __init__(
        self,
        bus=0,
        device=0,
        spd=1000000,
        pin_mode=10,
        pin_rst=-1,
        debug_level="WARNING",
    ):
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.spi.max_speed_hz = spd

        self.logger = logging.getLogger("mfrc522Logger")
        self.logger.addHandler(logging.StreamHandler())
        level = logging.getLevelName(debug_level)
        self.logger.setLevel(level)

        gpio_mode = GPIO.getmode()

        if gpio_mode is None:
            GPIO.setmode(pin_mode)
        else:
            pin_mode = gpio_mode

        if pin_rst == -1:
            if pin_mode == 11:
                pin_rst = 15
            else:
                pin_rst = 22

        GPIO.setup(pin_rst, GPIO.OUT)
        GPIO.output(pin_rst, 1)
        self.mfrc522_init()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_mfrc522()

    def mfrc522_reset(self):
        self.write_mfrc522(self.CommandReg, self.PCD_RESETPHASE)

    def write_mfrc522(self, addr, val):
        val = self.spi.xfer2([(addr << 1) & 0x7E, val])

    def read_mfrc522(self, addr):
        val = self.spi.xfer2([((addr << 1) & 0x7E) | 0x80, 0])
        return val[1]

    def close_mfrc522(self):
        self.spi.close()
        GPIO.cleanup()

    def set_bit_mask(self, reg, mask):
        tmp = self.read_mfrc522(reg)
        self.write_mfrc522(reg, tmp | mask)

    def clear_bit_mask(self, reg, mask):
        tmp = self.read_mfrc522(reg)
        self.write_mfrc522(reg, tmp & (~mask))

    def antenna_on(self):
        temp = self.read_mfrc522(self.TxControlReg)
        if ~(temp & 0x03):
            self.set_bit_mask(self.TxControlReg, 0x03)

    def antenna_off(self):
        self.clear_bit_mask(self.TxControlReg, 0x03)

    def mfrc522_to_card(self, command, send_data):
        back_data = []
        back_len = 0
        irqEn = 0x00
        waitIRq = 0x00
        n = 0

        if command == self.PCD_AUTHENT:
            irqEn = 0x12
            waitIRq = 0x10
        if command == self.PCD_TRANSCEIVE:
            irqEn = 0x77
            waitIRq = 0x30

        self.write_mfrc522(self.CommIEnReg, irqEn | 0x80)
        self.clear_bit_mask(self.CommIrqReg, 0x80)
        self.set_bit_mask(self.FIFOLevelReg, 0x80)

        self.write_mfrc522(self.CommandReg, self.PCD_IDLE)

        for d in send_data:
            self.write_mfrc522(self.FIFODataReg, d)

        self.write_mfrc522(self.CommandReg, command)

        if command == self.PCD_TRANSCEIVE:
            self.set_bit_mask(self.BitFramingReg, 0x80)

        i = 2000
        while True:
            n = self.read_mfrc522(self.CommIrqReg)
            i -= 1
            if ~((i != 0) and ~(n & 0x01) and ~(n & waitIRq)):
                break

        self.clear_bit_mask(self.BitFramingReg, 0x80)

        if i != 0:
            if (self.read_mfrc522(self.ErrorReg) & 0x1B) == 0x00:
                status = self.MI_OK

                if n & irqEn & 0x01:
                    status = self.MI_NOTAGERR

                if command == self.PCD_TRANSCEIVE:
                    n = self.read_mfrc522(self.FIFOLevelReg)
                    last_bits = self.read_mfrc522(self.ControlReg) & 0x07
                    if last_bits != 0:
                        back_len = (n - 1) * 8 + last_bits
                    else:
                        back_len = n * 8

                    if n == 0:
                        n = 1
                    if n > self.MAX_LEN:
                        n = self.MAX_LEN

                    for i in range(n):
                        back_data.append(self.read_mfrc522(self.FIFODataReg))
            else:
                status = self.MI_ERR
        else:
            status = self.MI_TIMEOUT

        self.logger.debug(f"({back_len}) {back_data}")

        return status, back_data, back_len

    def mfrc522_request(self, req_mode):
        self.write_mfrc522(self.BitFramingReg, 0x07)

        tag_type = [req_mode]
        status, back_data, back_len = self.mfrc522_to_card(
            self.PCD_TRANSCEIVE, tag_type
        )

        if (status != self.MI_OK) | (back_len != 0x10):
            status = self.MI_ERR

        return status, back_data, back_len

    def mfrc522_anticoll(self):
        ser_num = []

        self.write_mfrc522(self.BitFramingReg, 0x00)

        ser_num.append(self.PICC_ANTICOLL)
        ser_num.append(0x20)

        (status, backData, backBits) = self.mfrc522_to_card(
            self.PCD_TRANSCEIVE, ser_num
        )

        if status == self.MI_OK:
            if len(backData) == 5:
                ser_num_check = self.calculate_bcc(backData[:4])
                if ser_num_check != backData[4]:
                    status = self.MI_ERR
            else:
                status = self.MI_ERR

        return status, backData

    def calculate_crc(self, data):
        self.clear_bit_mask(self.DivIrqReg, 0x04)
        self.set_bit_mask(self.FIFOLevelReg, 0x80)

        for d in data:
            self.write_mfrc522(self.FIFODataReg, d)

        self.write_mfrc522(self.CommandReg, self.PCD_CALCCRC)
        i = 0xFF
        while True:
            n = self.read_mfrc522(self.DivIrqReg)
            i -= 1
            if not ((i != 0) and not (n & 0x04)):
                break

        return self.read_mfrc522(self.CRCResultRegL), self.read_mfrc522(
            self.CRCResultRegM
        )

    def mfrc522_select_tag(self, ser_num):
        assert len(ser_num) == 5
        buf = [self.PICC_SElECTTAG, 0x70]
        buf += ser_num

        (status, backData, backLen) = self.mfrc522_transeive_helper(buf)

        if (status == self.MI_OK) and (backLen == 0x18):
            self.logger.debug("Size: " + str(backData[0]))
            return backData[0]
        else:
            return 0

    def mfrc522_auth(self, auth_mode, block_addr, sectorkey, ser_num):
        # First byte should be the authMode (A or B)
        # Second byte is the trailerBlock (usually 7)
        buff = [auth_mode, block_addr]

        # Now we need to append the authKey which usually is 6 bytes of 0xFF
        buff += sectorkey

        # Next we append the first 4 bytes of the UID
        buff += ser_num[:4]

        # Now we start the authentication itself
        (status, backData, backLen) = self.mfrc522_to_card(self.PCD_AUTHENT, buff)

        # Check if an error occurred
        if not (status == self.MI_OK):
            self.logger.error("AUTH ERROR!!")
        if not (self.read_mfrc522(self.Status2Reg) & 0x08) != 0:
            self.logger.error("AUTH ERROR(status2reg & 0x08) != 0")

        # Return the status
        return status

    def mfrc522_stop_crypto1(self):
        self.clear_bit_mask(self.Status2Reg, 0x08)

    def mfrc522_read(self, block_addr):
        buff = [self.PICC_READ, block_addr]
        (status, backData, backLen) = self.mfrc522_transeive_helper(buff)
        if not (status == self.MI_OK):
            self.logger.error("Error while reading!")

        if len(backData) == 16:
            self.logger.debug("Sector " + str(block_addr) + " " + str(backData))
            return backData

        raise MFRC522Exception("No data read.")

    def mfrc522_write(self, block_addr: int, write_data):
        if len(write_data) != 16:
            raise MFRC522Exception("16 bytes needed")

        if not block_addr:
            self.logger.error(f"Writing to sector 0, manufacturer block.")

        if block_addr % 4 == 3:
            self.logger.warning(f"Writing to sector trailer block {block_addr}")

        buff = [self.PICC_WRITE, block_addr]
        (status, back_data, back_len) = self.mfrc522_transeive_helper(buff)
        if (
            not (status == self.MI_OK)
            or not (back_len == 4)
            or not ((back_data[0] & 0x0F) == 0x0A)
        ):
            status = self.MI_ERR

        self.logger.debug(
            "{} backdata &0x0F == 0x0A {}".format(back_len, back_data[0] & 0x0F)
        )
        if status == self.MI_OK:
            buf = []
            buf.extend(write_data)

            (status, back_data, back_len) = self.mfrc522_transeive_helper(buf)
            if (
                not (status == self.MI_OK)
                or not (back_len == 4)
                or not ((back_data[0] & 0x0F) == 0x0A)
            ):
                self.logger.error(f"Error while writing block {block_addr}")
            if status == self.MI_OK:
                self.logger.debug(f"Data written to block {block_addr}")

    def mfrc522_decrement(self, block_addr, delta):
        buff = [self.PICC_DECREMENT, block_addr]
        (status, backData, backLen) = self.mfrc522_transeive_helper(buff)
        if (
            not (status == self.MI_OK)
            or not (backLen == 4)
            or not ((backData[0] & 0x0F) == 0x0A)
        ):
            status = self.MI_ERR

        self.logger.debug(
            "%s backdata &0x0F == 0x0A %s" % (backLen, backData[0] & 0x0F)
        )
        if status == self.MI_OK:
            buf = self.value_to_bytes(delta)
            (status, backData, backLen) = self.mfrc522_transeive_helper(buf)
            if (
                not (status == self.MI_OK or status == self.MI_TIMEOUT)
                or not (backLen == 4)
                or not ((backData[0] & 0x0F) == 0x0A)
            ):
                self.logger.error("Error while writing")
            if status == self.MI_OK:
                self.logger.debug("Data written")

    def mfrc522_increment(self, block_addr, delta):
        buff = [self.PICC_INCREMENT, block_addr]
        (status, backData, backLen) = self.mfrc522_transeive_helper(buff)
        if (
            not (status == self.MI_OK)
            or not (backLen == 4)
            or not ((backData[0] & 0x0F) == 0x0A)
        ):
            status = self.MI_ERR

        self.logger.debug(
            "%s backdata &0x0F == 0x0A %s" % (backLen, backData[0] & 0x0F)
        )
        if status == self.MI_OK:
            buf = self.value_to_bytes(delta)
            (status, backData, backLen) = self.mfrc522_transeive_helper(buf)
            if (
                not (status == self.MI_OK or status == self.MI_TIMEOUT)
                or not (backLen == 4)
                or not ((backData[0] & 0x0F) == 0x0A)
            ):
                self.logger.error("Error while writing")
            if status == self.MI_OK:
                self.logger.debug("Data written")

    def mfrc522_transfer(self, block_addr):
        buff = [self.PICC_TRANSFER, block_addr]
        (status, backData, backLen) = self.mfrc522_transeive_helper(buff)
        if (
            not (status == self.MI_OK)
            or not (backLen == 4)
            or not ((backData[0] & 0x0F) == 0x0A)
        ):
            self.logger.error("Error while transfer")

    def mfrc522_transeive_helper(self, buff):
        crc = self.calculate_crc(buff)
        buff += crc
        return self.mfrc522_to_card(self.PCD_TRANSCEIVE, buff)

    def mfrc522_dump_classic1k(self, keys, uid):
        data = []
        for i in range(64):
            key_idx = i // 4
            status = self.mfrc522_auth(self.PICC_AUTHENT1A, i, keys[key_idx], uid)
            # Check if authenticated
            if status == self.MI_OK:
                try:
                    data += self.mfrc522_read(i)
                except MFRC522Exception:
                    pass
            else:
                status = self.mfrc522_auth(
                    self.PICC_AUTHENT1B, i, keys[key_idx + 1], uid
                )
                # Check if authenticated
                if status == self.MI_OK:
                    try:
                        data += self.mfrc522_read(i)
                    except MFRC522Exception:
                        pass
                self.logger.error("Authentication error")

        return data

    def mfrc522_init(self):
        self.mfrc522_reset()

        self.write_mfrc522(self.TModeReg, 0x8D)
        self.write_mfrc522(self.TPrescalerReg, 0x3E)
        self.write_mfrc522(self.TReloadRegL, 30)
        self.write_mfrc522(self.TReloadRegH, 0)

        self.write_mfrc522(self.TxAutoReg, 0x40)
        self.write_mfrc522(self.ModeReg, 0x3D)
        self.antenna_on()

    @staticmethod
    def value_to_bytes(value):
        return list(value.to_bytes(4, "little"))

    @staticmethod
    def check_value_block(block: bytes):
        return (
            int.from_bytes(block[0:4], "little")
            == ~int.from_bytes(block[4:8], "little") & 0xFFFFFFFF
            == int.from_bytes(block[8:12], "little")
        ) and (block[12] == block[14] == ~block[13] & 0xFF == ~block[15] & 0xFF)

    @staticmethod
    def format_value_block(value: int = 0, address: int = 0):
        value &= 0xFFFFFFFF
        address &= 0xFF

        return (
            value.to_bytes(4, "little")
            + (~value & 0xFFFFFFFF).to_bytes(4, "little")
            + value.to_bytes(4, "little")
            + (address.to_bytes(1, "little") + (~address & 0xFF).to_bytes(1, "little"))
            * 2
        )

    @staticmethod
    def calculate_bcc(data):
        return reduce(xor, data[:4])

    @classmethod
    def get_block_value(cls, block: bytes):
        if not cls.check_value_block(block):
            raise MFRC522Exception(f"{block.hex()} is not a valid value block")

        return int.from_bytes(block[:4], "little")
