#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2024-11-23
# modified: 2025-11-16

from machine import Pin

class PassiveInfrared(object):
    def __init__(self, pin=26):
        self._pir_pin = Pin(pin, Pin.IN, Pin.PULL_UP)

    @property
    def triggered(self):
        '''
        Returns True if triggered.
        '''
        return int(self._pir_pin.value()) == 1

#EOF
