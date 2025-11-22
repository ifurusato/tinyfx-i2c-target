#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Murray Altheim. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License.
#
# author:   Murray Altheim
# created:  2025-11-16
# modified: 2025-11-22

import random # for sample response

class Controller:
    '''
    A controller for command strings received from the I2CSlave.

    This is a generic controller and simply prints the command
    string to the console. It can be either modified directly
    or subclassed to provide specific application handling.

    This includes a sample method to return a random string, as
    a demonstration of how to return data upon a request.
    '''
    def __init__(self):
        self._chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        self._slave = None
        print('ready.')

    def set_slave(self, slave):
        '''
        Assigns the I2C slave and registers this controller's callback.
        Should be called by your main program after instantiating both.
        '''
        self._slave = slave
        self._slave.add_callback(self.on_command)

    def on_command(self, cmd):
        '''
        Callback invoked by I2C slave when a command is received and processed outside IRQ.
        Delegates to process() for handling.
        '''
        return self.process(cmd)

    def tick(self, delta_ms):
        '''
        Can be called from main to update based on a delta in milliseconds.
        '''
        pass

    def _get_random_string(self, n=8):
        return ''.join(self._chars[random.getrandbits(6) % len(self._chars)] for _ in range(n))

    def process(self, cmd):
        '''
        Processes the callback from the I2C slave, returning 'ACK' or 'ERR'.
        This will process up to three optional arguments: arg0, arg1, arg2.
        '''
        try:
            print("command string: '{}'".format(cmd))
            parts = cmd.lower().split()
            if len(parts) == 0:
                return 'ERR'
            # process command
            _cmd  = parts[0]
            _arg0 = parts[1] if len(parts) > 1 else None
            _arg1 = parts[2] if len(parts) > 2 else None
            _arg2 = parts[3] if len(parts) > 3 else None
            if _cmd == 'rand':
                n = 8 if _arg1 is None else int(_arg1)
                response = self._get_random_string(n)
                print("generated random '{}'".format(response))
                return response
            else:
                print("command: '{}'{}{}{}".format(
                        _cmd,
                        "; arg0: '{}'".format(_arg0) if _arg0 else '',
                        "; arg1: '{}'".format(_arg1) if _arg1 else '',
                        "; arg2: '{}'".format(_arg2) if _arg2 else ''))
            return 'ACK'
        except Exception as e:
            print("{} raised by controller: {}".format(type(e), e))
            return 'ERR'

#EOF
