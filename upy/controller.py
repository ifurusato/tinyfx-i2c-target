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

class Controller:

    def __init__(self):
        pass

    def process(self, cmd):
        '''
        Processes the callback from the I2C slave, returning an 'OK' or 'ERR' response.
        '''
        try:
            print("command received by controller: '{}'".format(cmd))

            return 'OK'
        except Exception as e:
            print("{} raised by controller: {}".format(type(e), e))
            return 'ERR'

#EOF
