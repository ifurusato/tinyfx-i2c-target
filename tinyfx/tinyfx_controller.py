#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Murray Altheim. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License.
#
# author:   Murray Altheim
# created:  2025-11-16
# modified: 2025-11-18

from tiny_fx import TinyFX
from manual_player import ManualPlayer
from settable import SettableFX
from settable_blink import SettableBlinkFX
from pir import PassiveInfrared
from colors import *
from controller import Controller

class TinyFxController(Controller):
    '''
    A TinyFX controller for command strings received from the I2CSlave.

    Commands include:
      play [sound-name]     play a sound
      ch[1-6] on|off        control channels
      all on|off            turn all channels on or off (including RGB LED)
      heartbeat on|off      blinking RGB LED
      color [name]          set RGB LED to color name (see colors.py)

    Setting the heartbeat or color will disable the other.
    PIR sensor functionality currently has not been tested.
    '''
    def __init__(self, blink_channels=None):
        super().__init__()
#       self._slave   = None
        if blink_channels is None:
            blink_channels = [False, False, False, False, False, False]
        if len(blink_channels) != 6:
            raise ValueError("blink_channels must have exactly 6 boolean values")
        self._tinyfx  = TinyFX(init_wav=True, wav_root='/sounds')
        self._rgbled  = self._tinyfx.rgb
        self._playing = False
        # channel definitions
        self._channel1_fx = self._get_channel(1, blink_channels[0])
        self._channel2_fx = self._get_channel(2, blink_channels[1])
        self._channel3_fx = self._get_channel(3, blink_channels[2])
        self._channel4_fx = self._get_channel(4, blink_channels[3])
        self._channel5_fx = self._get_channel(5, blink_channels[4])
        self._channel6_fx = self._get_channel(6, blink_channels[5])
        # set up the effects to play
        self._player = ManualPlayer(self._tinyfx.outputs)
        self._player.effects = [
            self._channel1_fx,
            self._channel2_fx,
            self._channel3_fx,
            self._channel4_fx,
            self._channel5_fx,
            self._channel6_fx
        ]
        # name map of channels (you can add aliases here)
        self._channel_map = {
            'ch1': self._channel1_fx,
            'ch2': self._channel2_fx,
            'ch3': self._channel3_fx,
            'ch4': self._channel4_fx,
            'ch5': self._channel5_fx,
            'ch6': self._channel6_fx
        }
        # heartbeat blink feature
        self._heartbeat_enabled     = False
        self._heartbeat_on_time_ms  = 50
        self._heartbeat_off_time_ms = 2950
        self._heartbeat_timer = 0
        self._heartbeat_state = False
        # PIR sensor (no Timer: you can poll it manually if used)
        self._pir_sensor    = PassiveInfrared()
        self._pir_triggered = False
        self._pir_enabled   = False # default disabled
        self.play('arming-tone')
        # ready.

#   def set_slave(self, slave):
#   def on_command(self, cmd):

    def _get_channel(self, channel, blinking=False):
        '''
        The channel argument is included in case you want to customise what
        is returned per channel, e.g., channel 1 below.
        '''
        if blinking:
            if channel == 1:
                # we use a more 'irrational' speed so that the two blinking channels almost never synchronise
                return SettableBlinkFX(speed=0.66723, phase=0.0, duty=0.25)
            else:
                return SettableBlinkFX(speed=0.5, phase=0.0, duty=0.015)
        else:
            return SettableFX(brightness=0.8)

    def tick(self, delta_ms):
        self._player.update(delta_ms)
        if self._heartbeat_enabled:
            self._heartbeat(delta_ms)

    def _heartbeat(self, delta_ms):
        self._heartbeat_timer += delta_ms
        if self._heartbeat_state:
            if self._heartbeat_timer >= self._heartbeat_on_time_ms:
                self._rgbled.set_rgb(0, 0, 0)
                self._heartbeat_state = False
                self._heartbeat_timer = 0
        else:
            if self._heartbeat_timer >= self._heartbeat_off_time_ms:
                self._rgbled.set_rgb(0, 64, 64)
                self._heartbeat_state = True
                self._heartbeat_timer = 0

    def process(self, cmd):
        '''
        Processes the callback from the I2C slave, returning 'OK' or 'ERR'.
        '''
        try:
            print("cmd: '{}'".format(cmd))
            parts = cmd.lower().split()
            if len(parts) == 0:
                return 'ERR'
            _command = parts[0]
            _action  = parts[1] if len(parts) > 1 else None
            _value   = parts[2] if len(parts) > 2 else None
            if _command in ['all', 'ch1', 'ch2', 'ch3', 'ch4', 'ch5', 'ch6'] and len(parts) == 2:
                print('action: {}'.format(_action))
                if _command == 'all':
                    if _action == 'on':
                        for fx in self._player.effects:
                            fx.set(True)
                        self._heartbeat_enabled = True
                    elif _action == 'off':
                        for fx in self._player.effects:
                            fx.set(False)
                        self._heartbeat_enabled = False
                        self._show_color('color black')
                    else:
                        return 'ERR'
                else:
                    fx = self._channel_map[_command]
                    if _action == 'on':
                        fx.set(True)
                    elif _action == 'off':
                        fx.set(False)
                    else:
                        return 'ERR'
                return 'OK'
            elif _command == "heartbeat":
                if _action == 'on':
                    self._heartbeat_enabled = True
                elif _action == 'off':
                    self._heartbeat_enabled = False
                else:
                    return 'ERR'
            elif _command == "color":
                self._heartbeat_enabled = False
                self._show_color(cmd)
            elif _command == "play":
                self.play(cmd)
            else:
                print("unrecognised command: '{}' (ignored)".format(cmd))
            return 'OK'
        except Exception as e:
            print("{} raised by controller: {}".format(type(e), e))
            return 'ERR'

    def play(self, cmd):
        print("playing sound for command: {}".format(cmd))
        try:
            self._playing = True
            parts = cmd.split()
            if len(parts) < 2:
                sound_name = cmd
            else:
                sound_name = parts[1]
            print('playing: {}…'.format(sound_name))
            file_name = '{}.wav'.format(sound_name)
            self._tinyfx.wav.play_wav(file_name)
        finally:
            self._playing = False

    def _show_color(self, cmd):
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
