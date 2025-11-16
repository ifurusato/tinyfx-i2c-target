#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2025-11-16
# modified: 2025-11-16
#
# A simplified MonoPlayer that doesn't use a Timer thread, allowing manual
# updates from the main loop to avoid interference with audio playback.

from picofx import Updateable

class ManualPlayer:
    '''
    A manual-update version of MonoPlayer that controls mono LED outputs
    without using a Timer thread. Call update(delta_ms) in your main loop.
    '''
    def __init__(self, mono_leds):
        self.__leds = mono_leds if isinstance(mono_leds, (tuple, list)) else [mono_leds]
        self.__num_leds = len(self.__leds)
        self.__effects = [None] * self.__num_leds
        self.__updateables = set()

    @property
    def effects(self):
        '''
        Returns a tuple of the current effects.
        '''
        return tuple(self.__effects)

    @effects.setter
    def effects(self, effect_list):
        '''
        Sets the effects list. Each effect should be callable and optionally
        inherit from Updateable to receive tick() calls.
        '''
        effect_list = effect_list if isinstance(effect_list, list) else [effect_list] * self.__num_leds
        if len(effect_list) > self.__num_leds:
            raise ValueError(f"`effect_list` must have a length less or equal to {self.__num_leds}")
        self.__updateables = set()
        for i, fx in enumerate(effect_list):
            self.__effects[i] = fx
            # if the effect is Updateable, add it to the set for ticking
            if isinstance(fx, Updateable):
                self.__updateables.add(fx)
        # clear out excess effects
        if len(effect_list) < self.__num_leds:
            for i in range(len(effect_list), self.__num_leds):
                self.__effects[i] = None

    def update(self, delta_ms):
        '''
        Manually update all effects and apply them to the LEDs.
        Call this in your main loop with the milliseconds elapsed since last call.
        '''
        # tick all updateable effects
        for fx in self.__updateables:
            fx.tick(delta_ms)
        # apply brightness to each LED based on effect output
        for i in range(self.__num_leds):
            if self.__effects[i] is not None:
                self.__leds[i].brightness(self.__effects[i]())

#EOF
