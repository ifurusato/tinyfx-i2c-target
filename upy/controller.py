#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Murray Altheim. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License.
#
# author:   Murray Altheim
# created:  2025-11-16
# modified: 2025-11-16

import _thread
import time

class Controller:
    def __init__(self):
        self._playing = False

    def process(self, cmd):
        '''
        Processes the callback from the I2C slave, returning 'OK' or 'ERR'.
        "play" commands are executed in a background thread if not already playing.
        Additional "play" commands during playback are ignored and return 'BUSy'.
        '''
        try:
            print("command received by controller: '{}'".format(cmd))
            if cmd.lower().startswith("play"):
                if self._playing:
                    print("playback already in progress, ignoring new 'play' command")
                    return "BSY"
                print("starting playback thread for command:", cmd)
                self._playing = True
                _thread.start_new_thread(self._play_sound, (cmd,))
            else:
                print("cmd: '{}'".format(cmd))
            print("ctrl: 'OK'")
            return 'OK'
        except Exception as e:
            print("{} raised by controller: {}".format(type(e), e))
            print("crl: 'ERR'")
            return 'ERR'

    def _play_sound(self, cmd):
        try:
            print("play: {}".format(cmd))
            # simulate actual playback work
            time.sleep(20)
            print("complete: {}".format(cmd))
        finally:
            self._playing = False

#EOF
