#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Murray Altheim. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Murray Altheim
# created:  2025-11-16
# modified: 2025-11-16

import os, sys
import time
import smbus2

# add ./upy/ to sys.path
if os.path.isdir("upy") and "upy" not in sys.path:
    sys.path.insert(0, "upy")

from upy.message_util import pack_message, unpack_message

__I2C_BUS  = 1
__I2C_ADDR = 0x43

def i2c_write_and_read(bus, address, out_msg):
    # write to the slave
    print("out_msg =", list(out_msg))
    bus.write_i2c_block_data(address, 0, list(out_msg))
    # wait a short but sufficient time for the slave to process and prepare the reply
    time.sleep(0.002)
    # try up to 2 times to ensure correct, valid response is received.
    for _ in range(2):
        resp_buf = bus.read_i2c_block_data(address, 0, 32)
        print('DEBUG: resp_buf =', resp_buf)
        msg_len = resp_buf[0]
        if 1 <= msg_len < 32:
            # got a plausible length, unpack normally
            resp_bytes = bytes(resp_buf[:msg_len+2])
            return resp_bytes
        # else, brief delay and retry once more
        time.sleep(0.003)
    # if still no plausible response, raise as before
    raise RuntimeError("Bad message length or slave not ready")

def send_and_receive(bus, address, message):
    out_msg = pack_message(message)
    try:
        resp_bytes = i2c_write_and_read(bus, address, out_msg)
        return unpack_message(resp_bytes)
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
