#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Murray Altheim. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Murray Altheim
# created:  2025-01-17
# modified: 2025-11-16

import sys
import time
from machine import I2CTarget
from machine import Pin

try:
    from upy.message_util import pack_message, unpack_message
except ImportError:
    from message_util import pack_message, unpack_message

I2C_ID = 0
I2C_ADDRESS = 0x43
# size for worst case (max 255 byte string)
BUFFER_SIZE = 1 + 255 + 1

class I2CSlave:
    '''
    Constructs an I2C slave at the configured bus (0) and address (0x43).
    '''
    def __init__(self):
        self._i2c = None
        self._mem = bytearray(BUFFER_SIZE)
        self._callback = None

    def enable(self):
        self._i2c = I2CTarget(I2C_ID, I2C_ADDRESS, mem=self._mem, scl=Pin(17), sda=Pin(16))
        self._i2c.irq(handler=self._irq_handler, 
                      trigger=I2CTarget.IRQ_END_READ | I2CTarget.IRQ_END_WRITE, 
                      hard=False)
        print('I2C slave enabled at address {:#04x}'.format(I2C_ADDRESS))

    def disable(self):
        if self._i2c:
            self._i2c.deinit()
            self._i2c = None
            print('I2C slave disabled')

    def add_callback(self, callback):
        self._callback = callback

    def _irq_handler(self, i2c_target):
        flags = i2c_target.irq().flags()
        if flags & I2CTarget.IRQ_END_WRITE:
            try:
                cmd_bytes = bytes(self._mem[:])
                try:
                    cmd = unpack_message(cmd_bytes)
                except Exception:
                    # fallback: ignore trailing zero padding, find plausible message length
                    msg_len = cmd_bytes[0]
                    cut_bytes = cmd_bytes[:msg_len+2]
                    cmd = unpack_message(cut_bytes)
#               print('received from master: {}'.format(cmd))
                response = 'ERR'
                if self._callback:
                    response = self._callback(cmd)
                else:
                    response = 'ACK'
                resp_bytes = pack_message(response)
                for i in range(BUFFER_SIZE):
                    self._mem[i] = 0
                self._mem[:len(resp_bytes)] = resp_bytes
#               print("DEBUG slave resp_bytes:", list(resp_bytes))
                time.sleep_us(50)
            except Exception as e:
                print('slave error during irq: {}'.format(e))
                # send ERR back
                resp_bytes = pack_message('ERR')
                for i in range(BUFFER_SIZE):
                    self._mem[i] = 0
                self._mem[:len(resp_bytes)] = resp_bytes
#               print("ERR DEBUG slave resp_bytes:", list(resp_bytes))

#EOF
