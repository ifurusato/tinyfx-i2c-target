#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Murray Altheim. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Murray Altheim
# created:  2025-01-21
# modified: 2025-11-16

import os, sys
import time
import traceback
import itertools
import smbus2

# add ./upy/ to sys.path
if os.path.isdir("upy") and "upy" not in sys.path:
    sys.path.insert(0, "upy")

from upy.message_util import pack_message, unpack_message

I2C_BUS = 1
I2C_ADDR = 0x43

def i2c_write_and_read(bus, address, out_msg):
    bus.write_i2c_block_data(address, 0, list(out_msg))
    time.sleep(0.001)
    resp_buf = bus.read_i2c_block_data(address, 0, 32)
    print('DEBUG: resp_buf =', resp_buf)
    msg_len = resp_buf[0]
    resp_bytes = bytes(resp_buf[:msg_len+2])
    return resp_bytes

def x_i2c_write_and_read(bus, address, out_msg):
    bus.write_i2c_block_data(address, 0, list(out_msg))
    time.sleep(0.001)
    # read in response, up to 32 bytes for max message: [len][data][crc8]
    # first byte is length; read that first to determine total
    in_len = bus.read_byte(address)
    resp = [in_len]
    # read the rest: payload + crc8
    resp_rest = bus.read_i2c_block_data(address, 0, in_len + 1)
    resp += resp_rest
    resp_bytes = bytes(resp)
    # read first byte (length)
    in_len = bus.read_byte(address)
    # read the rest of the message (payload + crc8) from offset 1
    resp_rest = bus.read_i2c_block_data(address, 1, in_len + 1)
    resp_bytes = bytes([in_len]) + bytes(resp_rest)
    return resp_bytes

def send_and_receive(bus, address, message):
    out_msg = pack_message(message)
    try:
        resp_bytes = i2c_write_and_read(bus, address, out_msg)
        response = unpack_message(resp_bytes)
        return response
    except Exception as e:
        print('I2C message error: {}'.format(e))
        return None

def main():
    print('opening I2C bus {} to address {:#04x}'.format(I2C_BUS, I2C_ADDR))
    with smbus2.SMBus(I2C_BUS) as bus:
        try:
            while True:
                user_msg = input('Enter command string to send ("quit" to exit): ')
                if user_msg.strip().lower() == 'quit':
                    break
                if len(user_msg) == 0:
                    continue
                response = send_and_receive(bus, I2C_ADDR, user_msg)
                print('Slave response: {}'.format(response))
        except KeyboardInterrupt:
            print('Ctrl-C caught, exiting…')
        except Exception as e:
            print('error: {}'.format(e))

if __name__ == '__main__':
    main()

#EOF
