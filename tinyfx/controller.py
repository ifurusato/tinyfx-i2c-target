#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Murray Altheim. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License.
#
# author:   Murray Altheim
# created:  2025-11-16
# modified: 2025-11-16

import time
from tiny_fx import TinyFX
from colors import*

class Controller:
    def __init__(self):
        self._playing = False
        self._slave   = None
        self._tinyfx  = TinyFX(init_wav=True, wav_root='/sounds')
        self._rgbled  = self._tinyfx.rgb

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

    def process(self, cmd):
        '''
        Processes the callback from the I2C slave, returning 'OK' or 'ERR'.
        '''
        try:
            print("command received by controller: '{}'".format(cmd))
            if cmd.lower().startswith("play"):
                self._play_sound(cmd)
            elif cmd.lower().startswith("color"):
                self._show_color(cmd)
            else:
                print("cmd: '{}'".format(cmd))
            print("ctrl: 'OK'")
            return 'OK'
        except Exception as e:
            print("{} raised by controller: {}".format(type(e), e))
            print("ctrl: 'ERR'")
            return 'ERR'

    def _play_sound(self, cmd):
        print("playing sound for command: {}".format(cmd))
        try:
            self._playing = True
            parts = cmd.split()
            if len(parts) < 2:
                print("ERROR: play command missing sound name.")
                return
            sound_name = parts[1]
            print('playing: {}…'.format(sound_name))
            file_name = '{}.wav'.format(sound_name)
            self._tinyfx.wav.play_wav(file_name)
        finally:
            self._playing = False

    def _show_color(self, cmd):
        from colors import get_color_by_name
        parts = cmd.split()
        if len(parts) < 2:
            print("ERROR: show color command missing color name.")
            return
        color_name = parts[1]
        color = get_color_by_name(color_name)
        if color:
            print('showing color: {}…'.format(color.description))
            self._rgbled.set_rgb(*color)
        else:
            print("ERROR: unknown color name: {}".format(color_name))

#EOF


