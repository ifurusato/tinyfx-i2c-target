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

def i2c_write_and_read(bus, address, message):
    '''
    Write a message and read the response.
    '''
    out_msg = pack_message(message)
    bus.write_i2c_block_data(address, 0, list(out_msg))
    time.sleep(0.002)  # brief delay for slave processing
    
    for _ in range(2):
        resp_buf = bus.read_i2c_block_data(address, 0, 32)
        # auto-detect and extract the real message
        if resp_buf and resp_buf[0] == 0 and len(resp_buf) > 2:
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
        time.sleep(0.003)
    raise RuntimeError("bad message length or slave not ready.")

def send_command(bus, address, command):
    '''
    Send a command and return acknowledgment status.
    Returns: "ACK", "ERR:code", or "READY"
    '''
    return i2c_write_and_read(bus, address, command)

def get_response(bus, address):
    '''
    Request the result of the previous command.
    Returns: "OK", "OK:data", "ERR:code", or "STALE"
    '''
    return i2c_write_and_read(bus, address, "RESPOND")

def send_and_receive(bus, address, command, get_result=True):
    '''
    Send a command and optionally get its execution result.
    
    Args:
        bus:        SMBus instance
        address:    I2C slave address
        command:    command string to send
        get_result: if True, waits for execution result; if False, only checks acknowledgment
    
    Returns:
        If get_result=False: acknowledgment ("ACK" or "ERR:code")
        If get_result=True: tuple of (acknowledgment, result)
    '''
    try:
        # Step 1: send command and get acknowledgment
        ack = send_command(bus, address, command)
        
        if not get_result:
            return ack
        
        # Step 2: get execution result
        if ack == "ACK":
            time.sleep(0.002)  # Give slave time to process
            result = get_response(bus, address)
            return (ack, result)
        else:
            # command was rejected, no result to fetch
            return (ack, None)
            
    except Exception as e:
        print('I2C communication error: {}'.format(e))
        return None if not get_result else (None, None)

def main():
    print('opening I2C bus {} to address {:#04x}'.format(__I2C_BUS, __I2C_ADDR))
    with smbus2.SMBus(__I2C_BUS) as bus:
        try:
            # check initial state
            initial = get_response(bus, __I2C_ADDR)
            print('initial state: {}'.format(initial))
            
            while True:
                user_msg = input('\nEnter command ("quit" to exit, "?" for help): ')
                if user_msg.strip().lower() == 'quit':
                    break
                if user_msg.strip() == 'help':
                    print('Commands:')
                    print('  ch[1-6] on|off  - Control channel')
                    print('  all on|off      - Control all channels')
                    print('  heartbeat on|off - Control heartbeat')
                    print('  color [name]    - Set RGB LED color')
                    print('  play [sound]    - Play sound')
                    print('  RESPOND         - Get pending response')
                    continue
                if len(user_msg) == 0:
                    continue
                # send command and get full result
                result = send_and_receive(bus, __I2C_ADDR, user_msg, get_result=True)
                if result:
                    ack, response = result
                    response = response if response else ack
                    print('response: {}'.format(response))

        except KeyboardInterrupt:
            print('\nCtrl-C caught, exiting…')
        except OSError as e:
            if e.errno == 5:
                print('ERROR: the I2C target is not available.')
            else:
                print('OSError raised connecting to target: {}'.format(e))
        except Exception as e:
            print('{} raised connecting to target: {}'.format(type(e), e))

if __name__ == '__main__':
    main()

#EOF
