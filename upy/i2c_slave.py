#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Murray Altheim. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Murray Altheim
# created:  2025-01-17
# modified: 2025-01-21

import sys
import time
#from pyb import LED
from machine import I2CTarget
from machine import Pin
from colorama import Fore, Style

from core.logger import Logger, Level
from command import Command
from payload import Payload
from response import Response
from motor_controller import MotorController

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class I2CSlave(object):
    # Memory map constants
    CMD_OFFSET  = 0                        # command buffer starts at byte 0
    RSP_OFFSET  = Payload.PACKET_SIZE      # response buffer starts after command buffer
    MEMORY_SIZE = 2 * Payload.PACKET_SIZE  # total memory: command + response
    '''
    I2C slave controller that receives commands and sends responses using
    memory-mapped buffers.
    
    Memory Map:
        Bytes 0-22:  command buffer (23 bytes for Payload)
        Bytes 23-45: response buffer (23 bytes for Payload)
    '''
    def __init__(self, level=Level.INFO):
        '''
        Initialize I2C slave controller.

        The SDA and SCL pins on the STM32 depend on which bus is used:

          I2C1:  PB7 (SDA), PB6 (SCL)
          I2C2:  PB11 (SDA), PB10 (SCL)
          I2C3:  PC9 (SDA), PA8 (SCL)
        
        Args:
            level:    logging level
        '''
        self._log = Logger('i2c-slave', level=level)
        self._i2c_id = 0
        self._i2c_address = 0x43
#       self._led      = LED(1)
        self._i2c      = None
        self._debug    = True
        self._tx_count = 0
        self._mem      = bytearray(self.MEMORY_SIZE)
        self._motor_controller = MotorController(level)
        # keepalive timer:
        self._last_command_time_ms = 0
        self._keepalive_timeout_ms = 200
        self._log.info('ready on bus {} at 0x{:02X}'.format(self._i2c_id, self._i2c_address))

    def _clear_response_buffer(self):
        '''
        Clear the response buffer.
        '''
        self._mem[self.RSP_OFFSET:self.RSP_OFFSET + Payload.PACKET_SIZE] = bytearray(Payload.PACKET_SIZE)
    
    def enable(self):
        '''
        Start I2C slave and register IRQ handler.
        '''
        if self._i2c:
            self._log.debug('I2C slave already enabled.')
            return
        self._log.info('starting I2C slave controller…')
        try:
            # create I2C target with memory buffer
            self._i2c = I2CTarget(self._i2c_id, self._i2c_address, mem=self._mem, scl=Pin(17), sda=Pin(16))
            # register IRQ handler for end of read/write transactions
            # using soft IRQ (hard=False) since we have a memory buffer
            self._i2c.irq(handler=self._irq_handler, 
                         trigger=I2CTarget.IRQ_END_READ | I2CTarget.IRQ_END_WRITE,
                         hard=False)
            self._log.info('I2C slave enabled on address {:#04x}.'.format(self._i2c_address))
            self._log.info(Fore.WHITE + 'I2C slave running; press Ctrl+C to stop.')
        except Exception as e:
            self._log.error('{} raised starting I2C target {}'.format(type(e), e))
            sys.print_exception(e)
    
    def disable(self):
        '''
        Stop I2C slave.
        '''
        if self._i2c:
            self._i2c.deinit()
            self._i2c = None
            self._log.info('I2C slave disabled')
 
    def _irq_handler(self, i2c_target):
        '''
        Handle I2C events from master.
        '''
        flags = i2c_target.irq().flags()
        if flags & I2CTarget.IRQ_END_WRITE:
            # master wrote a command - process it immediately
            try:
#               self._led.on()
                # update timestamp for keepalive
                self._last_command_time_ms = time.ticks_ms()
                # parse command payload from command buffer
                cmd_bytes = bytes(self._mem[self.CMD_OFFSET:self.CMD_OFFSET + Payload.PACKET_SIZE])
                cmd_payload = Payload.from_bytes(cmd_bytes)
#               if self._debug:
#                   self._log.debug('rx: {}'.format(cmd_payload))
                # process command based on Command
                command = Command.from_code(cmd_payload.code)
                if command is Command.PING:
                    self._handle_ping()
                elif command is Command.STOP:
                    self._handle_stop()
                elif command is Command.GO:
                    self._handle_go(cmd_payload)
                elif command is Command.REQUEST:
                    self._handle_request()
                elif command is Command.ENABLE:
                    self._handle_enable()
                elif command is Command.DISABLE:
                    self._handle_disable()
                else:
                    self._handle_error(1, 'unknown command: {}'.format(cmd_payload.code))
                self._tx_count += 1

            except ValueError as e:
                # bad payload - silently ignore sync header issues (i2cdetect probing)
                error_msg = str(e)
                if 'invalid sync header' not in error_msg:
                    self._log.error('payload error: {}'.format(e))
                    self._handle_error(2, error_msg)
                else:
                    self._log.warning('payload warning: {}'.format(e))
                    self._handle_error(3, error_msg)
                    
            except Exception as e:
                self._log.error('{} raised in irq handler: {}'.format(type(e), e))
                sys.print_exception(e)
                self._handle_error(4, str(e))
        
    def _send_response(self, command, pfwd, sfwd, paft, saft):
        '''
        Write response Payload to response buffer.
        '''
        try:
            if not isinstance(command, Command):
                raise TypeError('expected command, not {}'.format(type(command)))
            response = Payload(command, pfwd, sfwd, paft, saft)
            response_bytes = response.to_bytes() 
            # write to response buffer atomically using slice assignment
            self._mem[self.RSP_OFFSET:self.RSP_OFFSET + len(response_bytes)] = response_bytes
            time.sleep_us(50) # make sure response is committed before IRQ completes

        except Exception as e:
            self._log.error('{} raised sending response: {}'.format(type(e), e))
            sys.print_exception(e)
        finally:
#           self._led.off()
            pass

    # keepalive timer ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    def check_keepalive(self):
        '''
        Check if keepalive timeout has expired and stop motors if needed.
        Must be called periodically from main loop.
        '''
        if self._motor_controller.enabled and self._last_command_time_ms > 0:
            elapsed = time.ticks_diff(time.ticks_ms(), self._last_command_time_ms)
            if elapsed > self._keepalive_timeout_ms:
                self._log.warning('keepalive timeout - stopping motors (connection lost)')
                self._motor_controller.stop()
                self._clear_response_buffer()
                self._last_command_time_ms = 0 # reset to prevent repeated stops

    # command handlers ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
    
    def _handle_ping(self):
        '''
        Respond to PING with another PING.
        '''
        if self._debug:
            self._log.info('command: PING')
        self._send_response(Command.PING, 0.3, 0.3, 0.3, 0.3)
    
    def _handle_stop(self):
        '''
        Handle STOP command - stop all motors.
        '''
        if self._debug:
            self._log.info(Fore.RED + Style.DIM + '[{:05d}] command: STOP'.format(self._tx_count))
        _response = self._motor_controller.stop()
        if _response is Response.OKAY:
            _speeds = self._motor_controller.get_speeds()
            self._send_response(Command.ACK, *_speeds)
        else:
            self._send_response(Command.ERROR, 0.0, 0.0, 0.0, 0.0) # return error code in position 1
    
    def _handle_go(self, payload):
        '''
        Handle GO command - set motor speeds.
        
        Args:
            payload: Command Payload containing motor speeds
        '''
        if self._debug:
            self._log.info(Fore.GREEN + '[{:05d}] command: GO (pfwd={:.2f}, sfwd={:.2f}, paft={:.2f}, saft={:.2f})'.format(
                    self._tx_count, payload.pfwd, payload.sfwd, payload.paft, payload.saft))
        _response = self._motor_controller.go(payload.pfwd, payload.sfwd, payload.paft, payload.saft)
        if _response is Response.OKAY:
            _speeds = self._motor_controller.get_speeds()
            self._send_response(Command.ACK, *_speeds)
        else:
            self._send_response(Command.ERROR, 0.0, 0.0, 0.0, 0.0) # TODO return error code in position 1

    def _handle_request(self):
        '''
        Handle REQUEST command - return current motor state.
        '''
        if self._debug:
            self._log.info('command: REQUEST')
        self._log.info(Fore.BLUE + 'command: REQUEST')
        _speeds = self._motor_controller.get_speeds()
        self._send_response(Command.RESPONSE, *_speeds)
    
    def _handle_enable(self):
        '''
        Handle ENABLE command - enable motors.
        '''
        self._log.info('command: ENABLE')
        self._motor_controller.enable()
        self._last_command_time_ms = time.ticks_ms() # for keepalive
        self._send_response(Command.ACK, 0.0, 0.0, 0.0, 0.0)
    
    def _handle_disable(self):
        '''
        Handle DISABLE command - disable motors.
        '''
        self._log.info('command: DISABLE')
        self._motor_controller.disable()
        self._last_command_time_ms = 0  # clear keepalive timestamp when disabled
        self._send_response(Command.ACK, 0.0, 0.0, 0.0, 0.0)
        time.sleep_us(100)  # give master time to read the ACK response
        self._clear_response_buffer()

    def _handle_error(self, error_code, message):
        '''
        Send ERROR response.
        
        Args:
            error_code: Error code (encoded in pfwd as integer)
            message: Error message (for logging only)
        '''
        self._log.error('Error {}: {}'.format(error_code, message))
        self._send_response(Command.ERROR, float(error_code), 0.0, 0.0, 0.0)

#EOF
