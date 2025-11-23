#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2025-11-16
# modified: 2025-11-23

import sys
import time
from machine import I2CTarget, Pin

try:
    from upy.message_util import pack_message, unpack_message
except ImportError:
    from message_util import pack_message, unpack_message

__IS_STM32    = False
__IS_ESP32    = False

__I2C_ID      = 0
__I2C_ADDRESS = 0x43
__BUF_LEN     = 258


class I2CSlave:
    '''
    Constructs an I2C slave at the configured bus (0) and address (0x43).
    '''
    def __init__(self):
        self._i2c = None
        self._single_chunk = bytearray(32)
        self._tx_len = 0
        self._rx_len = 0
        self._last_rx_len = 0
        self._tx_buf = bytearray(__BUF_LEN)
        self._rx_buf = bytearray(__BUF_LEN)
        for i in range(__BUF_LEN):
            self._rx_buf[i] = 0
        init_msg = pack_message("ACK")
        self._tx_len = len(init_msg)
        for i in range(self._tx_len):
            self._tx_buf[i] = init_msg[i]
        self._new_cmd = False
        self._callback = None

    def enable(self):
        '''
        Enables the I2C slave and sets up IRQ handling.
        '''
        triggers = (I2CTarget.IRQ_WRITE_REQ | I2CTarget.IRQ_END_WRITE |
                    I2CTarget.IRQ_READ_REQ | I2CTarget.IRQ_END_READ)
        if __IS_STM32:
            __I2C_ID  = 1 # configure for your board; pins are pre-set for each bus
            self._i2c = I2CTarget(__I2C_ID, __I2C_ADDRESS)
        elif __IS_ESP32:

            # AttributeError: type object 'I2CTarget' has no attribute 'IRQ_WRITE_REQ'

            # this configuration is for the UM TinyS3; configure for your board
            self._i2c = I2CTarget(__I2C_ID, __I2C_ADDRESS, scl=Pin(9), sda=Pin(8))
        else: # RP2040
            self._i2c = I2CTarget(__I2C_ID, __I2C_ADDRESS, scl=Pin(17), sda=Pin(16))

        self._i2c.irq(self._irq_handler, trigger=triggers, hard=True)

        print('I2C slave enabled at address {:#04x}'.format(__I2C_ADDRESS))

    def disable(self):
        if self._i2c:
            self._i2c.deinit()
            self._i2c = None

    def add_callback(self, callback):
        '''
        Registers a callback to process/unpack received commands.
        The callback accepts a single ASCII string and returns a string response.
        '''
        self._callback = callback

    def _irq_handler(self, i2c):
        flags = i2c.irq().flags()
        if flags & I2CTarget.IRQ_WRITE_REQ:
            n = i2c.readinto(self._single_chunk)
            if n and n > 0:
                for i in range(n):
                    self._rx_buf[self._rx_len] = self._single_chunk[i]
                    self._rx_len += 1
        if flags & I2CTarget.IRQ_END_WRITE:
            self._last_rx_len = self._rx_len
            self._new_cmd = True
        if flags & I2CTarget.IRQ_READ_REQ:
            i2c.write(self._tx_buf)

    def check_and_process(self):
        WAIT = True # wait for the full message before unpacking
        if self._new_cmd:
            time.sleep_ms(5)  # Small delay to ensure IRQ completes
            self._new_cmd = False
            try:
                if WAIT:
                    raw = self._rx_buf[:self._last_rx_len]
                    if len(raw) < 2:  # must have at least register + length
                        return  # incomplete, wait
                    msg_len = raw[1]
                    expected_total = 1 + 1 + msg_len + 1  # reg + length + payload + crc
                    if len(raw) < expected_total:
                        return  # full message not yet in buffer
                    rx_bytes = raw[1:1 + 1 + msg_len + 1]
                else:
                    raw = self._rx_buf[:self._last_rx_len]
                    # skip the first byte (register address from I2C master)
                    if raw and len(raw) > 1:
                        msg_len = raw[1]  # Length of payload
                        if msg_len > 0 and len(raw) >= msg_len + 3:
                            rx_bytes = bytes(raw[1:msg_len + 3])
                        else:
                            rx_bytes = bytes(raw[1:])
                    else:
                        raise ValueError("message too short")
                cmd = unpack_message(rx_bytes)
                if self._callback:
                    response = self._callback(cmd)
                    if not response:
                        response = "ACK"
                else:
                    response = "ACK"

            except Exception as e:
                print("ERROR: {} raised during unpacking/processing: {}".format(type(e), e))
                sys.print_exception(e)
                response = "ERR"
            # clear buffer state for next message
            self._rx_len = 0
            self._last_rx_len = 0
            # clear the buffer contents
            for i in range(__BUF_LEN):
                self._rx_buf[i] = 0
            try:
                resp_bytes = pack_message(str(response))
            except Exception as e:
                print("ERROR: {} raised during packing response: {}".format(type(e), e))
                sys.print_exception(e)
                resp_bytes = pack_message("ERR")
            rlen = len(resp_bytes)
            for i in range(rlen):
                self._tx_buf[i] = resp_bytes[i]
            self._tx_len = rlen

#EOF
