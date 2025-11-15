#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Murray Altheim. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Murray Altheim
# created:  2025-10-21
# modified: 2025-10-22

from colorama import Fore, Style

from core.logger import Logger, Level
from response import Response

class MotorController(object):
    '''
    A mock controller for four motors. 

    Args:
        config:   application-level configuration
        level:    log level
    '''
    def __init__(self, level=Level.INFO):
        self._log = Logger('motor-ctrl', level=level)
        self._log.info('initialising motor controller…')
        self._pfwd = 0.0
        self._sfwd = 0.0
        self._paft = 0.0
        self._saft = 0.0
        self._enabled = False
        self._debug   = False
        self._log.info('ready.')

    def get_speeds(self):
        return ( self._pfwd, self._sfwd, self._paft, self._saft )

    def stop(self):
        '''
        Stop all motors immediately.
        '''
        self._log.info(Fore.RED + 'STOP')
        self._pfwd = 0.0
        self._sfwd = 0.0
        self._paft = 0.0
        self._saft = 0.0
        return Response.OKAY

    def go(self, pfwd, sfwd, paft, saft):
        '''
        Set the speeds of each of the four motors.
        '''
        self._log.info(Fore.GREEN + 'GO (pfwd={:.2f}, sfwd={:.2f}, paft={:.2f}, saft={:.2f})'.format(pfwd, sfwd, paft, saft))
        self._pfwd = pfwd
        self._sfwd = sfwd
        self._paft = paft
        self._saft = saft
        return Response.OKAY

    @property
    def enabled(self):
        return self._enabled

    def enable(self):
        '''
        Enable the motor controller.
        '''
        self._log.info('enabled.')
        self._enabled = True
            
    def disable(self):
        '''
        Disable the motor controller.
        '''
        self.stop()
        self._enabled = False
        self._log.info('disabled.')
            
    def close(self):
        self.disable()
        self._log.info('closed.')

#EOF
