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

import sys
import time
from i2c_slave import I2CSlave
from controller import Controller

# auto-clear: remove cached modules to force reload
for mod in ['main', 'i2c_slave', 'controller']:
    if mod in sys.modules:
        del sys.modules[mod]

def main():
    blink_channels = [False, False, False, True, False, False] # channel 4 blinks
    controller = Controller(blink_channels)
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
