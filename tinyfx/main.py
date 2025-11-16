#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Murray Altheim. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Murray Altheim
# created:  2025-11-16
# modified: 2025-11-16

import sys
import time
from i2c_slave import I2CSlave
from controller import Controller

# auto-clear: remove cached modules to force reload
for mod in ['main', 'i2c_slave']:
    if mod in sys.modules:
        del sys.modules[mod]

def main():
    controller = Controller()
    slave = I2CSlave()
    slave.add_callback(controller.process)
    slave.enable()
    try:
        while True:
            slave.check_and_process()
            time.sleep_ms(1)
#           time.sleep(1)
    except KeyboardInterrupt:
        print('\nCtrl-C caught; exiting…')
        slave.disable()

main()

#EOF
