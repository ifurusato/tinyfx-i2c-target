#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Murray Altheim. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License.
#
# author:   Murray Altheim
# created:  2025-11-16
# modified: 2025-11-16

from tiny_fx import TinyFX
from manual_player import ManualPlayer
from settable import SettableFX
from settable_blink import SettableBlinkFX
from pir import PassiveInfrared
from colors import *
#from colors import get_color_by_name

class Controller:
    '''
    A controller for command strings received from the I2CSlave.

    This is a generic controller and simply prints the command
    string to the console. It can be either modified directly
    or subclassed to provide specific application handling.
    '''
    def __init__(self):
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
        return self._process(cmd)

    def tick(self, delta_ms):
        '''
        Can be called from main to update based on a delta in milliseconds.
        '''
        pass

    def process(self, cmd):
        '''
        Processes the callback from the I2C slave, returning 'OK' or 'ERR'.
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
            print("command: '{}'; arg0: {}; arg1: {}".format(
                    _cmd,
                    "'{}'".format(_arg0) if _arg0 else 'n/a',
                    "'{}'".format(_arg1) if _arg1 else 'n/a'))
            return 'OK'
        except Exception as e:
            print("{} raised by controller: {}".format(type(e), e))
            return 'ERR'

#EOF
