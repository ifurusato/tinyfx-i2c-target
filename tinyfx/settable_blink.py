#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2024-09-07
# modified: 2025-11-16
#
# A Tiny FX device that blinks according to values set via a method.

from picofx import Cycling

class SettableBlinkFX(Cycling):
    def __init__(self, interval=0.1, speed=1, phase=0.0, duty=0.5):
        self.interval = interval
        super().__init__(speed)
        self.phase = phase
        self.duty  = duty
        self._state = False
        self.__time = 0

    def set(self, state):
        self._state = state

    def get(self):
        return self._state

    def toggle(self):
        self._state = not self._state

    def __call__(self):
        if self._state:
            percent = (self.__offset + self.phase) % 1.0
            return 1.0 if percent < self.duty else 0.0
        else:
            return 0.0

#EOF
