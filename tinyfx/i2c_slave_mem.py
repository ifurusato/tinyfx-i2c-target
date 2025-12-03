#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2025-11-16
# modified: 2025-12-04
#
# ESP32-specific I2C slave implementation using memory buffer approach.

import sys
import time
from machine import I2CTarget, Pin

try:
    from upy.message_util import pack_message, unpack_message
except ImportError:
    from message_util import pack_message, unpack_message


class I2CSlave:
    __I2C_ID      = 0
    __I2C_SCL_PIN = 2
    __I2C_SDA_PIN = 3
    __I2C_ADDRESS = 0x42
    __BUF_LEN     = 258
    '''
    An I2C slave using a memory buffer approach.
    
    The I2CTarget acts as an I2C memory device that the master
    can read/write using readfrom_mem() and writeto_mem() calls.
    Uses defaults if arguments not supplied.
    
    Memory layout:
    - Address 0x00: RX buffer (master writes commands here)
    - Address 0x80: TX buffer (master reads responses from here)

    Args:
        i2c_id:       the optional I2C bus ID (0)
        i2c_address:  the optional I2C address (0x42)
        scl_pin:      the optional SCL pin number (pin 2)
        sda_pin:      the optional SDA pin number (pin 3)
    '''
    def __init__(self, i2c_id=None, i2c_address=None, sda_pin=None, scl_pin=None):
        # configuration
        self._i2c_id      = I2CSlave.__I2C_ID
        self._sda_pin     = sda_pin if sda_pin else I2CSlave.__I2C_SDA_PIN
        self._scl_pin     = scl_pin if scl_pin else I2CSlave.__I2C_SCL_PIN
        self._i2c_address = i2c_address if i2c_address else I2CSlave.__I2C_ADDRESS
        # state variables
        self._i2c         = None
        self._memory      = bytearray(I2CSlave.__BUF_LEN * 2)  # Double size: RX + TX regions
        self._rx_start    = 0
        self._tx_start    = I2CSlave.__BUF_LEN
        # initialize TX buffer with ACK message
        init_msg = pack_message("ACK")
        for i, b in enumerate(init_msg):
            self._memory[self._tx_start + i] = b
        self._tx_len      = len(init_msg)
        self._callback    = None
        self._last_rx_snapshot = bytearray(I2CSlave.__BUF_LEN)
        self._process_next = False

    def enable(self):
        '''
        Enables the I2C slave as a memory device.
        '''
        self._i2c = I2CTarget(self._i2c_id, self._i2c_address, scl=Pin(self._scl_pin), sda=Pin(self._sda_pin))
        # set up memory buffer that master can access
        # the I2CTarget will automatically handle memory reads/writes
        self._i2c.write(self._memory)
        # set up IRQ to detect when master accesses memory
        self._i2c.irq(self._irq_handler, trigger=I2CTarget.IRQ_END_WRITE | I2CTarget.IRQ_END_READ)
        print('I2C memory slave enabled on I2C{} at address {:#04x} (SCL={}, SDA={})'.format(
                self._i2c_id, self._i2c_address, self._scl_pin, self._sda_pin))
        print('  RX buffer at offset 0x00')
        print('  TX buffer at offset 0x{:02x}'.format(self._tx_start))

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
        '''
        IRQ handler for memory access events.
        '''
        flags = i2c.irq().flags()
        if flags & I2CTarget.IRQ_END_WRITE:
            # master wrote to our memory - copy current state for processing
            try:
                # read back the memory to get what master wrote
                i2c.readinto(self._memory)
                # flag that we should process the RX buffer
                self._process_next = True
            except:
                pass
        if flags & I2CTarget.IRQ_END_READ:
            # master read from our memory - update TX buffer if needed
            try:
                # reload memory with current TX data
                i2c.write(self._memory)
            except:
                pass

    def check_and_process(self):
        '''
        Process received commands and prepare responses.
        Must be called regularly from main loop. 
        '''
        if not self._process_next:
            return
        
        self._process_next = False
        
        try:
            # take snapshot of RX buffer
            for i in range(I2CSlave.__BUF_LEN):
                self._last_rx_snapshot[i] = self._memory[self._rx_start + i]
            raw = self._last_rx_snapshot
            # parse the message (same format as before)
            if len(raw) < 2:
                return  # Incomplete
            msg_len = raw[1]
            expected_total = 1 + 1 + msg_len + 1  # reg + length + payload + crc
            if len(raw) < expected_total:
                return  # full message not yet received
            rx_bytes = raw[1:1 + 1 + msg_len + 1]
            cmd = unpack_message(rx_bytes)
            # process command
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
        # clear RX buffer
        for i in range(I2CSlave.__BUF_LEN):
            self._memory[self._rx_start + i] = 0
        # prepare response in TX buffer
        try:
            resp_bytes = pack_message(str(response))
            for i, b in enumerate(resp_bytes):
                self._memory[self._tx_start + i] = b
            self._tx_len = len(resp_bytes)
            # update the I2C memory
            if self._i2c:
                self._i2c. write(self._memory)
        except Exception as e:
            print("ERROR: {} raised during packing response: {}".format(type(e), e))
            sys.print_exception(e)

#EOF
