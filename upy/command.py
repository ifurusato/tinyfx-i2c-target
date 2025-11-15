#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Murray Altheim. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Murray Altheim
# created:  2025-07-04
# modified: 2025-10-23
#
# A pseudo-enum for Payload commands.

class Command:
    _instances = []

    def __init__(self, index, code, description):
        self._index = index
        self._code = code
        self._description = description
        Command._instances.append(self)

    @property
    def index(self):
        return self._index

    @property
    def code(self):
        return self._code

    @property
    def description(self):
        return self._description

    def __str__(self):
        return self._code

    def __repr__(self):
        return "<command({}, {})".format(self._code, self._description)

    @classmethod
    def all(cls):
        return cls._instances

    @classmethod
    def from_index(cls, index):
        for inst in cls._instances:
            if inst.index == index:
                return inst
        raise ValueError("no Command with index '{}'".format(index))

    @classmethod
    def from_code(cls, code):
        for inst in cls._instances:
            if inst.code == code:
                return inst
        raise ValueError("no Command with code '{}'".format(code))

# instances
Command.COLOR       = Command( 0, "CO", "show color")       # sets a status RGB LED color
Command.STOP        = Command( 1, "ST", "stop")             # stop all motors
Command.GO          = Command( 2, "GO", "go")               # set speed of four motors
Command.ACK         = Command( 3, "AK", "acknowledge")      # acknowledge message
Command.NACK        = Command( 4, "NK", "not acknowledge")  # fail to acknowledge
Command.PING        = Command( 5, "PN", "ping")             # ping sanity check
Command.REQUEST     = Command( 6, "RQ", "request status")   # request motor controller status
Command.RESPONSE    = Command( 7, "RP", "status response")  # response to request
Command.ENABLE      = Command( 8, "EN", "enable")           # enable motor controller
Command.DISABLE     = Command( 9, "DI", "disable")          # disable motor controller
Command.ERROR       = Command(10, "ER", "error")            # send error code

#EOF
