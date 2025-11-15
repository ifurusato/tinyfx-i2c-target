#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Murray Altheim. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Murray Altheim
# created:  2025-10-21
# modified: 2025-10-21

import sys
import time
from i2c_slave import I2CSlave
from core.logger import Logger, Level

# auto-clear: Remove cached modules to force reload
for mod in ['main', 'i2c_slave', 'payload']:
    if mod in sys.modules:
        del sys.modules[mod]

# ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
def main():

    _slave = None
    _slave = I2CSlave(level=Level.INFO)
    _slave.enable()
    try:
        while True:
            _slave.check_keepalive()
            time.sleep_ms(50) # check every 50ms
    except KeyboardInterrupt:
        print('\nCtrl-C caught; exiting…')
        _slave.disable()

# auto-start when imported
main()

#EOF
