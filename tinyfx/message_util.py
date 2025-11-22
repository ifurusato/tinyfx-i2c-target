#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2025-11-16
# modified: 2025-11-16

import sys

try:
    from upy.crc8_table import CRC8_TABLE
except ImportError:
    from crc8_table import CRC8_TABLE

def calculate_crc8(data):
    crc = 0
    for b in data:
        crc = CRC8_TABLE[crc ^ b]
    return crc

def pack_message(payload_str):
    '''
    Pack a string payload into i2c message: [length][payload_bytes][crc8]
    payload_str: ASCII string (or convertible to bytes)
    returns: bytes object to transmit
    '''
    payload_bytes = payload_str.encode('ascii')
    length = len(payload_bytes)
    if length > 255:
        raise ValueError('payload too long (max 255 bytes)')
    msg = bytes([length]) + payload_bytes
    crc = calculate_crc8(msg)
    return msg + bytes([crc])

def unpack_message(msg_bytes):
    '''
    Unpack message from [length][payload][crc8]. Return payload string if CRC ok, else raise ValueError.
    '''
    if len(msg_bytes) < 2:
        raise ValueError('message too short')
    length = msg_bytes[0]
    if len(msg_bytes) != length + 2:
        raise ValueError('bad message length (expected {}, got {})'.format(length+2, len(msg_bytes)))
    payload_bytes = msg_bytes[1:1+length]
    crc_in_msg = msg_bytes[-1]
    crc_check = calculate_crc8(msg_bytes[:-1])
    if crc_in_msg != crc_check:
        raise ValueError('crc8 mismatch')
    return payload_bytes.decode('ascii')

#EOF
