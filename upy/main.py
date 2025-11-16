#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Murray Altheim. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Murray Altheim
# created:  2025-10-21
# modified:  2025-11-16

import sys
import time
from i2c_slave import I2CSlave
from controller import Controller

def main():
    controller = Controller()
    slave = I2CSlave()
    slave.add_callback(controller.process)
    slave.enable()
    try:
        while True:
            time.sleep_ms(50)
    except KeyboardInterrupt:
        print('\nCtrl-C caught; exiting…')
        slave.disable()

# auto-start when imported
main()

#EOF
