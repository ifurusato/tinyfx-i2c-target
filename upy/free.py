#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Murray Altheim. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Murray Altheim
# created:  2025-06-20
# modified: 2025-06-27

import os
from colorama import Fore, Style
from logger import Logger, Level

_log = Logger('free', level=Level.INFO)
try:
    SAFE_LIMIT = 8000 # warning threshold

    stat = os.statvfs('/flash')
    block_size   = stat[0] # f_bsize
    total_blocks = stat[2] # f_blocks
    free_blocks  = stat[3] # f_bfree
    total_bytes  = block_size * total_blocks
    free_bytes   = block_size * free_blocks
    used_bytes   = total_bytes - free_bytes
    used_percent = (used_bytes / total_bytes) * 100
    color = Fore.GREEN if free_bytes > SAFE_LIMIT else Fore.RED
    width = 8
    _log.info(Fore.CYAN + "total flash size: " + Fore.CYAN + "{:>{width},} bytes".format(total_bytes, width=width))
    _log.info(Fore.CYAN + "free flash space: " + color + "{:>{width},} bytes".format(free_bytes, width=width))
    _log.info(Fore.CYAN + "used flash space: " + color + "{:>{width},} bytes ({:>5.2f}%)".format(used_bytes, used_percent, width=width))

except Exception as e:
    _log.error('{} raised by free: {}'.format(type(e), e))
finally:
    _log = None

#EOF
