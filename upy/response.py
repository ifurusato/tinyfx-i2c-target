#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Murray Altheim. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Murray Altheim
# created:  2025-05-06
# modified: 2025-10-23
#
# motor controller response codes as a pseudo-enum.

class Response:
    _instances = []

    def __init__(self, value: int):
        self._value  = value
        Response._instances.append(self)

# define response codes
Response.OKAY     = Response(0)
Response.FAIL     = Response(1)

#EOF
