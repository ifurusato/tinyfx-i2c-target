#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2025-01-16
# modified: 2025-01-22
#
# TinyFX I2C Master Control for MicroPython
#
# To use from the REPL, import with:
#
#   > from tinyfx_ctrl_mpy import send
#
# Example usage:
#
#   > send("ch1 on")       # for channels 1-6
#   > send("color blue")   # color names defined in colors.py
#   > send("play beep")    # play sounds/beep.wav

import sys
import time
from machine import I2C, Pin

# be sure to copy both message_util.py and crc8_table.py to the microcontroller
from message_util import pack_message, unpack_message

# auto-clear: remove cached modules to force reload
for mod in ['main']:
    if mod in sys.modules:
        del sys.modules[mod]

# ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

# I2C Configuration (configure for specific board)
__I2C_BUS_ID  = 1       # I2C bus ID (0 or 1 on most boards)
__I2C_SCL_PIN = 9       # GPIO pin for SCL
__I2C_SDA_PIN = 8       # GPIO pin for SDA
__I2C_FREQ    = 100000  # I2C frequency (100kHz)
__I2C_ADDR    = 0x43    # TinyFX I2C address

# global I2C instance
_i2c = None

def _get_i2c():
    '''
    Get or create the I2C instance.
    '''
    global _i2c
    if _i2c is None:
#       print('Initializing I2C bus {} at address {:#04x}'.format(__I2C_BUS_ID, __I2C_ADDR))
#       print('SCL: GPIO{}, SDA: GPIO{}, Freq: {}Hz'.format(__I2C_SCL_PIN, __I2C_SDA_PIN, __I2C_FREQ))
        _i2c = I2C(__I2C_BUS_ID,
                   scl=Pin(__I2C_SCL_PIN),
                   sda=Pin(__I2C_SDA_PIN),
                   freq=__I2C_FREQ)
    return _i2c

def i2c_write_and_read(i2c, address, message):
    '''
    Write a message to the I2C slave and read the response.
    '''
    out_msg = pack_message(message)
    out_msg = bytearray([0]) + out_msg # changed for mcu-based communication
    i2c.writeto(address, out_msg)
    time.sleep_ms(2)
    for _ in range(2):
        resp_buf = bytearray(32)
        i2c.readfrom_into(address, resp_buf)
        # auto-detect and extract the real message
        if resp_buf[0] == 0 and len(resp_buf) > 2:
            # skip first byte, interpret the second as length
            msg_len = resp_buf[1]
            if 1 <= msg_len < 32:
                resp_bytes = bytes(resp_buf[1:1+msg_len+2])
                return unpack_message(resp_bytes)
        else:
            msg_len = resp_buf[0]
            if 1 <= msg_len < 32:
                resp_bytes = bytes(resp_buf[:msg_len+2])
                return unpack_message(resp_bytes)
        time.sleep_ms(3)
    raise RuntimeError("bad message length or slave not ready.")

def send(message):
    '''
    Send a command to the TinyFX slave and get result.
    '''
    i2c = _get_i2c()
    # Step 1: Send command, get ACK/ERR
    ack = i2c_write_and_read(i2c, __I2C_ADDR, message)
    print('acknowledgment: {}'.format(ack))
    # Step 2: Get result
    time.sleep_ms(2)
    result = i2c_write_and_read(i2c, __I2C_ADDR, "RESPOND")
    print('result: {}'.format(result))
    return (ack, result)

# print usage instructions on import
print("\nTinyFX I2C Master Control")
print("\nready for:  send('command')")
print()

#EOF
