#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Murray Altheim. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Murray Altheim
# created:  2025-06-12
# modified: 2025-10-23

import struct
from command import Command

try:
    from upy.crc8_table import CRC8_TABLE # master
except ImportError:
    from crc8_table import CRC8_TABLE # slave

class Payload:
    # sync header: 'zz' for human-readability. To switch to a binary header, just uncomment the next line.
    SYNC_HEADER = b'\x7A\x7A'
    PACK_FORMAT = '<2sffff'  # 2-char code, 4 floats
    PAYLOAD_SIZE = struct.calcsize(PACK_FORMAT) # size of code+floats only, no CRC or header
    CRC_SIZE = 1
    PACKET_SIZE = len(SYNC_HEADER) + PAYLOAD_SIZE + CRC_SIZE  # header + payload + crc
    VARIABLE_FORMAT = "{:2s} {:.1f} {:.1f} {:.1f} {:.1f}"
    FIXED_FORMAT    = "{:>2} {:5.1f} {:5.1f} {:5.1f} {:5.1f}"

    def __init__(self, command, pfwd, sfwd, paft, saft):
        if not isinstance(command, Command):
            raise TypeError('expected command, not {}'.format(type(command)))
        self._command = command
        self._code = command.code
        self._pfwd = pfwd
        self._sfwd = sfwd
        self._paft = paft
        self._saft = saft

    @property
    def command(self):
        return self._command

    @property
    def code(self):
        return self._code

    @property
    def pfwd(self):
        return self._pfwd

    @property
    def sfwd(self):
        return self._sfwd

    @property
    def paft(self):
        return self._paft

    @property
    def saft(self):
        return self._saft

    @property
    def rgb(self):
        return self._pfwd, self._sfwd, self._paft

    @property
    def values(self):
        return self._pfwd, self._sfwd, self._paft, self._saft

    @property
    def speeds(self):
        '''
        An alias for values when they are assumed a four motor speeds.
        '''
        return self.values

    def as_log(self):
        return Payload.VARIABLE_FORMAT.format(
            self._code, self._pfwd, self._sfwd, self._paft, self._saft
        )

    def __repr__(self):
        code_str = self._code.decode('utf-8') if isinstance(self._code, bytes) else self._code
        return "Payload(code={:>2}, pfwd={:7.2f}, sfwd={:7.2f}, paft={:7.2f}, saft={:7.2f})".format(
            code_str, self._pfwd, self._sfwd, self._paft, self._saft
        )

    def __eq__(self, other):
        if not isinstance(other, Payload):
            return NotImplemented
        return (
            self._code == other._code
            and self._pfwd == other._pfwd
            and self._sfwd == other._sfwd
            and self._paft == other._paft
            and self._saft == other._saft
        )

    def to_bytes(self):
        '''
        A convenience method that calls __bytes__(). This is probably safer as in
        certain cases __bytes__() doesn't get triggered correctly in MicroPython.
        '''
        return self.__bytes__()

    def __bytes__(self):
        # pack the data into bytes (code, floats)
        _code  = self._code.encode('ascii') if isinstance(self._code, str) else self._code
        packed = struct.pack(self.PACK_FORMAT, _code, self._pfwd, self._sfwd, self._paft, self._saft)
        crc = self.calculate_crc8(packed)
        return Payload.SYNC_HEADER + packed + bytes([crc])

    @classmethod
    def from_bytes(cls, packet):
        if len(packet) != cls.PACKET_SIZE:
            raise ValueError("invalid packet size: {}".format(len(packet)))
        if packet[:len(Payload.SYNC_HEADER)] != Payload.SYNC_HEADER:
            raise ValueError("invalid sync header")
        data_and_crc = packet[len(Payload.SYNC_HEADER):]
        data, crc = data_and_crc[:-1], data_and_crc[-1]
        calc_crc = cls.calculate_crc8(data)
        if crc != calc_crc:
            raise ValueError("CRC mismatch.")
        code, pfwd, sfwd, paft, saft = struct.unpack(cls.PACK_FORMAT, data)
        command = Command.from_code(code.decode('ascii'))
        return cls(command, pfwd, sfwd, paft, saft)

    @staticmethod
    def calculate_crc8(data: bytes) -> int:
        crc = 0
        for b in data:
            crc = CRC8_TABLE[crc ^ b]
        return crc

    @staticmethod
    def encode_int(value_32_bit_int):
        '''
        Encode a 32-bit int into four floats in range 0–255.0.
        '''
        masked_value = value_32_bit_int & 0xFFFFFFFF
        float0 = float((masked_value >> 24) & 0xFF)
        float1 = float((masked_value >> 16) & 0xFF)
        float2 = float((masked_value >> 8) & 0xFF)
        float3 = float(masked_value & 0xFF)
        return float0, float1, float2, float3

    @staticmethod
    def decode_to_int(f0, f1, f2, f3):
        '''
        Decode a 32-bit int from four floats.
        '''
        byte0 = int(f0)
        byte1 = int(f1)
        byte2 = int(f2)
        byte3 = int(f3)
        reconstructed_int = (byte0 << 24) | (byte1 << 16) | (byte2 << 8) | byte3
        return reconstructed_int

    @staticmethod
    def _encode_int(value):
        '''
        Encode a 32-bit int into four floats in range 0–255.0.
        '''
        if not (0 <= value <= 0xFFFFFFFF):
            raise ValueError("value out of 32-bit unsigned range")
        b0 = (value >> 24) & 0xFF
        b1 = (value >> 16) & 0xFF
        b2 = (value >> 8) & 0xFF
        b3 = value & 0xFF
        return [float(b) for b in (b0, b1, b2, b3)]

    @staticmethod
    def _decode_to_int(values):
        '''
        Decode a 32-bit int from four floats.
        '''
        if len(values) != 4:
            raise ValueError("expected four floats.")
        b0, b1, b2, b3 = [int(round(f)) & 0xFF for f in values]
        return (b0 << 24) | (b1 << 16) | (b2 << 8) | b3

#EOF
