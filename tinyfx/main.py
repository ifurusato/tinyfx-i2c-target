#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2025-11-16
# modified: 2025-11-18

import sys
import time
from i2c_slave import I2CSlave
from controller import Controller
from tinyfx_controller import TinyFxController

__USE_TINYFX = True # set False to use the generic Controller

# auto-clear: remove cached modules to force reload
for mod in ['main', 'i2c_slave', 'controller']:
    if mod in sys.modules:
        del sys.modules[mod]

def main():
    if __USE_TINYFX:
        blink_channels = [True, False, False, True, False, False] # channel 1 and 4 blinks
        controller = TinyFxController(blink_channels)
    else: # use generic controller
        controller = Controller()
    slave = I2CSlave()
    slave.add_callback(controller.process)
    slave.enable()
    last_time = time.ticks_ms()
    try:
        while True:
            current_time = time.ticks_ms()
            delta_ms = time.ticks_diff(current_time, last_time)
            last_time = current_time
            controller.tick(delta_ms)
            slave.check_and_process()
            time.sleep_ms(10)
    except KeyboardInterrupt:
        print('\nCtrl-C caught; exiting…')
        slave.disable()

main()

#EOF
