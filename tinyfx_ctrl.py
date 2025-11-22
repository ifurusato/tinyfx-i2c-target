#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2025-11-16
# modified: 2025-11-22

import os, sys
import time
import smbus2

# add ./tinyfx/ to sys.path
if os.path.isdir("tinyfx") and "tinyfx" not in sys.path:
    sys.path.insert(0, "tinyfx")

from tinyfx.message_util import pack_message, unpack_message

# ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

__I2C_BUS  = 1      # the I2C bus number; on a Raspberry Pi the default is 1
__I2C_ADDR = 0x43   # the I2C address used to connect to the TinyFX

def i2c_write_and_read(bus, address, out_msg):
    bus.write_i2c_block_data(address, 0, list(out_msg))
    time.sleep(0.002)
    for _ in range(2):
        resp_buf = bus.read_i2c_block_data(address, 0, 32)
        # auto-detect and extract the real message
        if resp_buf and resp_buf[0] == 0 and len(resp_buf) > 2:
            # skip first byte, interpret the second as length
            msg_len = resp_buf[1]
            if 1 <= msg_len < 32:
                resp_bytes = bytes(resp_buf[1:1+msg_len+2])
                return resp_bytes
        else:
            msg_len = resp_buf[0]
            if 1 <= msg_len < 32:
                resp_bytes = bytes(resp_buf[:msg_len+2])
                return resp_bytes
        time.sleep(0.003)
    raise RuntimeError("bad message length or slave not ready.")

def send_and_receive(bus, address, message):
    '''
    Send a message and return the response.

    If the message begins with a '!' character this is treated as a data request,
    causing three transactions to occur. The first sends the original message but
    its response is thrown away, as it will be an ACK. The second retrieves the
    data, and the third cleans the buffer.

    This is due to a requirement on slave IRQ processing that limits the ability
    to return the status of the current transaction (meaning the response returned
    is always from the previous transaction).
    '''
    data_request = message.startswith('!')
    if data_request:
        message = message[1:]
    try:
        if data_request:
            data_request_bytes = i2c_write_and_read(bus, address, pack_message(message))
#           print("throwaway message: '{}'".format(unpack_message(data_request_bytes)))
            time.sleep(0.002)
        response_bytes = i2c_write_and_read(bus, address, pack_message('get'))
        data_response = unpack_message(response_bytes)
#       print("response: '{}'".format(data_response))
        if data_request:
            time.sleep(0.002)
            cleanup_bytes = i2c_write_and_read(bus, address, pack_message('clean'))
#           print("cleanup message: '{}'".format(unpack_message(cleanup_bytes)))
        return data_response
    except Exception as e:
        print('I2C message error: {}'.format(e))
        return None

def main():
    print('opening I2C bus {} to address {:#04x}'.format(__I2C_BUS, __I2C_ADDR))
    with smbus2.SMBus(__I2C_BUS) as bus:
        try:
            while True:
                user_msg = input('Enter command string to send ("quit" to exit): ')
                if user_msg.strip().lower() == 'quit':
                    break
                if len(user_msg) == 0:
                    continue
                response = send_and_receive(bus, __I2C_ADDR, user_msg)
                print('response: {}'.format(response))
        except KeyboardInterrupt:
            print('Ctrl-C caught, exiting…')
        except Exception as e:
            print('error: {}'.format(e))

if __name__ == '__main__':
    main()

#EOF
