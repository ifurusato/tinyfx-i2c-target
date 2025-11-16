#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2025-06-20
# modified: 2025-11-16

import os

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
    width = 8
    print("total flash size: {:>{width},} bytes".format(total_bytes, width=width))
    print("free flash space: {:>{width},} bytes".format(free_bytes, width=width))
    print("used flash space: {:>{width},} bytes ({:>5.2f}%)".format(used_bytes, used_percent, width=width))

except Exception as e:
    print('ERROR: {} raised by free: {}'.format(type(e), e))

#EOF
