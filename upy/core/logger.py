#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2019-2025 by Murray Altheim. All rights reserved. This file is part
# of the K-Series Robot Operating System (KROS) project, released under the MIT
# License. Please see the LICENSE file included as part of this package.
#
# author:   Murray Altheim
# created:  2020-01-14
# modified: 2025-11-11
#
# A simplification of the KROS Logger class, just using print statements and
# not supporting log-to-file, log suppression, etc. As MicroPython does not
# support Enums, a workaround is provided for Level.

from colorama import Fore, Style

def enum(**enums: int):
    return type('Enum', (), enums)

Level = enum(DEBUG=10, INFO=20, WARN=30, ERROR=40, CRITICAL=50)
# e.g., levels = (Level.DEBUG, Level.INFO)

# ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
class Logger(object):

    __color_debug    = Fore.BLUE   + Style.DIM
    __color_info     = Fore.CYAN   + Style.NORMAL
    __color_warning  = Fore.YELLOW + Style.NORMAL
    __color_error    = Fore.RED    + Style.NORMAL
    __color_reset    = Style.RESET_ALL

    def __init__(self, name="log", level=Level.INFO):
        '''
        Writes to the console with the provided level.

        Args:
            name:   the name identified with the log output
            level:  the log level
        '''
        self._name         = name
        self._level        = level
        self._include_timestamp = True
        self._date_format  = '%Y-%m-%dT%H:%M:%S'
        self.__DEBUG_TOKEN = 'DEBUG'
        self.__INFO_TOKEN  = 'INFO '
        self.__WARN_TOKEN  = 'WARN '
        self.__ERROR_TOKEN = 'ERROR'
        self.__FATAL_TOKEN = 'FATAL'
        self._mf           = '{}{} : {}{}'

    @property
    def name(self):
        '''
        Return the name of this Logger.
        '''
        return self._name

    @property
    def level(self):
        '''
        Return the level of this logger.
        '''
        return self._level

    def is_at_least(self, level):
        '''
        Returns True if the current log level is less than or equals the argument.
        '''
        return self._level >= level

    def close(self):
        '''
        Not supported in this implementation, but raises no exception when called.
        '''
        pass

    # ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    def debug(self, message):
        '''
        Prints a debug message.
        '''
        if self.is_at_least(Level.DEBUG):
            print(self._mf.format(Logger.__color_debug, self.__DEBUG_TOKEN, message, Logger.__color_reset))

    def info(self, message):
        '''
        Prints an informational message.
        '''
        if self.is_at_least(Level.INFO):
            print(self._mf.format(Logger.__color_info, self.__INFO_TOKEN, message, Logger.__color_reset))

    def warning(self, message):
        '''
        Prints a warning message.
        '''
        if self.is_at_least(Level.WARN):
            print(self._mf.format(Logger.__color_warning, self.__WARN_TOKEN, message, Logger.__color_reset))

    def error(self, message):
        '''
        Prints an error message.
        '''
        if self.is_at_least(Level.ERROR):
            print(self._mf.format(Logger.__color_error, self.__ERROR_TOKEN, message, Logger.__color_reset))

#EOF
