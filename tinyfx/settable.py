#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2024-12-17
# modified: 2025-11-16
#
# A Tiny FX device that responds immediately to set() commands.

from picofx import Updateable

class SettableFX(Updateable):

    def __init__(self, brightness=1.0):
        self._brightness = brightness
        self._state = False

    def __call__(self):
        return self._brightness if self._state else 0.0

    def set(self, state):
        self._state = state

    def get(self):
        return self._state

    def toggle(self):
        self._state = not self._state

    def tick(self, delta_ms):
        pass

#EOF
