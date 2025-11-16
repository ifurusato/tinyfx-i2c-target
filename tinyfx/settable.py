#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2024 by Murray Altheim. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Murray Altheim
# created:  2024-08-28
# modified: 2024-09-18
#
# A Tiny FX device whose state can be set via a method call.

from machine import Pin
from picofx import Updateable

class SettableFX(Updateable):
    def __init__(self, brightness=1.0, interval=0.1):
        self.interval = interval
        self._brightness = brightness
        self.__value = 0.0
        self._state = False
        self.__time = 0

    def __call__(self):
        return self.__value

    def set(self, state):
        self._state = state

    def get(self):
        return self._state

    def toggle(self):
        self._state = not self._state

    def tick(self, delta_ms):
        self.__time += delta_ms

        # Check if the interval has elapsed
        if self.__time >= (self.interval * 1000):
            self.__time -= (self.interval * 1000)
            if self._state:
                self.__value = self._brightness
            else:
                self.__value = 0.0

#EOF
