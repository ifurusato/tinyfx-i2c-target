#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Murray Altheim. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Murray Altheim
# created:  2025-01-21
# modified: 2025-11-16

import os, sys
import time
import traceback
import itertools
from datetime import datetime as dt
from math import isclose
import smbus2
from colorama import init, Fore, Style
init()

from core.logger import Level, Logger
from core.component import Component
from core.config_loader import ConfigLoader

# add ./upy/ to sys.path
if os.path.isdir("upy") and "upy" not in sys.path:
    sys.path.insert(0, "upy")

from payload import Payload
from command import Command
from response import Response

class I2CMasterController(Component):
    CMD_OFFSET = 0
    RSP_OFFSET = Payload.PACKET_SIZE
    '''
    I2C Master controller for sending command Payloads to STM32 slave
    and receiving response Payloads.

    This is a Component subclass that follows the standard enable/disable lifecycle.
    '''
    def __init__(self, config, i2c_id=1, i2c_address=0x43, level=Level.INFO):
        '''
        Initialize I2C master controller.

        Args:
            config:       application configuration
            i2c_id:       I2C bus number (default 1 for Raspberry Pi)
            i2c_address:  slave device I2C address (default 0x43)
            level:        logging level
        '''
        self._log = Logger('i2c-master', level)
        Component.__init__(self, self._log, suppressed=False, enabled=False)
        self._i2c_id      = i2c_id
        self._i2c_address = i2c_address
        self._bus         = None
        self._retry_count = 5
        self._tx_count    = 0
        self._error_count = 0
        self._timeout     = 1.0  # seconds
        self._keepalive_test = False # tests the keepalive timeout
        self.set_tx_delay(100) # 100μs default (works down to 1μS or zero in practice)
        self._log.info('initialized for bus {}, slave at {:#04x}'.format(i2c_id, i2c_address))

    def set_tx_delay(self, usec):
        self._log.info(Fore.BLUE + 'tx delay: {:5.1f}µs'.format(usec))
        self._tx_delay_usec = usec

    def enable(self):
        '''
        Enable the I2C master. Performs PING/ACK handshake with slave.
        Raises exception if slave doesn't respond correctly.
        '''
        if self.enabled:
            self._log.warning('already enabled.')
            return
        try:
            # open I2C bus
            self._bus = smbus2.SMBus(self._i2c_id)
            self._log.info('I2C bus opened')
            # perform initial PING/ACK handshake
            self._log.info('sending PING to slave...')
            ping_payload = Payload(Command.PING, 0.0, 0.0, 0.0, 0.0)
            response_payload = self._send_command(ping_payload)
            self._log.info(Fore.MAGENTA + 'PING response: {}'.format(response_payload))
            if response_payload.command is not Command.PING:
                raise Exception('PING failed: expected PING, got {}'.format(response_payload.code))
            self._log.info(Fore.GREEN + 'PING successful, slave responded with ACK' + Style.RESET_ALL)
            time.sleep(0.05)
            enable_payload = Payload(Command.ENABLE, 0.0, 0.0, 0.0, 0.0)
            response_payload = self._send_command(enable_payload)
            self._log.info(Fore.MAGENTA + 'ENABLE response: {}'.format(response_payload))
            Component.enable(self)

        except Exception as e:
            self._log.error('enable failed: {}'.format(e))
            if self._bus:
                self._bus.close()
                self._bus = None
            raise

    def _send_command(self, payload, retry=True):
        '''
        Send command Payload to slave and read response.
        '''
        if not self._bus:
            raise Exception('I2C bus not open.')
        attempts = self._retry_count if retry else 1
        last_error = None

        for attempt in range(attempts):
            try:
                self._tx_count += 1
                _start_time = dt.now()
                # write command payload to command buffer (block write)
                cmd_bytes = payload.to_bytes()
                self._bus.write_i2c_block_data(self._i2c_address, self.CMD_OFFSET, list(cmd_bytes))
#               self._log.debug('sent command: {}'.format(payload))
                # short delay to allow slave IRQ to complete
                time.sleep(self._tx_delay_usec / 1_000_000)
                # read response buffer in ONE transaction (block read)
                rsp_bytes = self._bus.read_i2c_block_data(self._i2c_address, self.RSP_OFFSET, Payload.PACKET_SIZE)
                response_payload = Payload.from_bytes(bytes(rsp_bytes))
#               self._log.debug('received response: {}'.format(response_payload))
                # check for error response
                if response_payload.command == Command.ERROR:
                    error_code = int(response_payload.pfwd)
                    self._log.warning('slave returned ERROR code {}'.format(error_code))
                else:
                    _elapsed_ms = (dt.now() - _start_time).total_seconds() * 1000.0
                    if attempt > 0:
                        self._log.info(Fore.YELLOW + 'transaction complete on attempt {}: elapsed: {:4.2f}ms elapsed ({}/{} err/tx)'.format(
                                attempt + 1, _elapsed_ms, self._error_count, self._tx_count))
                    else:
                        self._log.info(Fore.GREEN + 'transaction complete: elapsed: {:4.2f}ms elapsed ({}/{} err/tx)'.format(
                                _elapsed_ms, self._error_count, self._tx_count))
                return response_payload

            except ValueError as e:
                self._error_count += 1
                last_error = e
                self._log.warning('payload error (attempt {}/{}): {}'.format(attempt + 1, attempts, e))
                if attempt < attempts - 1:
                    time.sleep(0.05)

            except Exception as e:
                self._error_count += 1
                last_error = e
                self._log.warning('I2C error (attempt {}/{}): {}'.format(attempt + 1, attempts, e))
                if attempt < attempts - 1:
                    time.sleep(0.05)

        raise Exception('command failed after {} attempts: {}'.format(attempts, last_error))

    def stop_motors(self):
        '''
        Send STOP command to immediately stop all motors.
        '''
        if not self.enabled:
            self._log.warning('not enabled, cannot send STOP')
            return None

        self._log.info('sending STOP command')
        stop_payload = Payload(Command.STOP, 0.0, 0.0, 0.0, 0.0)
        return self._send_command(stop_payload)

    def set_motor_speeds(self, pfwd, sfwd, paft, saft):
        '''
        Send GO command with motor speeds.
        '''
        if not self.enabled:
            self._log.warning('not enabled, cannot set motor speeds')
            return None
#       self._log.debug('setting motor speeds: pfwd={:4.2f}, sfwd={:4.2f}, paft={:4.2f}, saft={:4.2f}'.format(pfwd, sfwd, paft, saft))
        go_payload = Payload(Command.GO, pfwd, sfwd, paft, saft)
        return self._send_command(go_payload)

    def request_status(self):
        '''
        Send REQUEST command to query slave status.
        '''
        if not self.enabled:
            self._log.warning('not enabled, cannot request status')
            return None

        _start_time = dt.now()
        self._log.info('requesting status from slave')
        request_payload = Payload(Command.REQUEST, 0.0, 0.0, 0.0, 0.0)
        response_payload = self._send_command(request_payload)
        _elapsed_ms = int((dt.now() - _start_time).total_seconds() * 1000.0)
        self._log.info(Fore.YELLOW + 'transaction complete: elapsed: {}ms'.format(_elapsed_ms))
        # sanity check: REQUEST must get RESPONSE, not ACK
        if response_payload != Command.RESPONSE:
#           raise ValueError('REQUEST command returned {} instead of RESPONSE'.format(response_payload.code))
            self._log.warning('REQUEST command returned {} instead of RESPONSE'.format(response_payload.code))
        return response_payload

    def disable(self):
        '''
        Disable the I2C master.
        '''
        if self.enabled:
            if not self._keepalive_test:
                try:
                    # Send DISABLE command to slave
                    disable_payload = Payload(Command.DISABLE, 0.0, 0.0, 0.0, 0.0)
                    self._send_command(disable_payload, retry=False)
                except Exception as e:
                    self._log.warning('error sending DISABLE: {}'.format(e))
            Component.disable(self)

    def close(self):
        '''
        Close the I2C master and bus.
        '''
        if self._bus:
            try:
                self._bus.close()
                self._log.info('I2C bus closed')
            except Exception as e:
                self._log.warning('error closing bus: {}'.format(e))
            finally:
                self._bus = None

        return Component.close(self)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main():

    DELAY_TUNING_TEST   = True   # used to tune the transaction delay (0-2000µs)

    '''
    Test the I2C Master Controller.
    '''
    master      = None
    digital_pot = None

    __IOE_AVAILABLE = False
    try:
        import ioexpander as io
        from hardware.digital_pot import DigitalPotentiometer
        __IOE_AVAILABLE = True
    except ModuleNotFoundError:
        pass

    try:

        _log = Logger('test', level=Level.INFO)

        # read YAML configuration
        _level = Level.INFO
        config = ConfigLoader(Level.INFO).configure()
        _value = 0.0

        # create master controller
        _log.info('creating I2C Master Controller…')
        master = I2CMasterController(config, i2c_id=1, i2c_address=0x43, level=Level.INFO)

        if DELAY_TUNING_TEST:

            if __IOE_AVAILABLE:
                _log.info('creating digital potentiometer…')
                try:
                    digital_pot = DigitalPotentiometer(config, level=_level)
                    digital_pot.set_output_range(0.0, 1.0)
                    # initially set delay
                    _value = digital_pot.get_scaled_value(False) # values 0.0-1.0
                except Exception as e:
                    _log.error('no digital pot available.')
                    digital_pot = None
                    __IOE_AVAILABLE = False

                _delay_usec = _value * 2000.0
                master.set_tx_delay(_delay_usec)

            _log.info('enabling (PING/ACK handshake)…')
            master.enable()

            _counter = itertools.count()
            _log.info('starting delay tuning…  (Ctrl-C to exit)')
            while True:

                _value = 0.3
                if __IOE_AVAILABLE:
                    _value = digital_pot.get_scaled_value(False) # values 0.0-1.0
                _target_speed = 1.0 - abs((_value * 2.0) - 1.0)
                _log.info(Fore.MAGENTA + 'target speed: {:4.2f}'.format(_target_speed))

                _delay_usec = _value * 2000.0
                master.set_tx_delay(_delay_usec)
                if isclose(_target_speed, 0.0, abs_tol=0.08):
                    if __IOE_AVAILABLE:
                        digital_pot.set_black() # only on digital pot
#                   _motor_controller.set_speed(Orientation.ALL, 0.0)

                    _log.info('stopping motors…')
                    response = master.stop_motors()
#                   _log.info(Fore.GREEN + 'response: {}'.format(response))

                else:
                    if __IOE_AVAILABLE:
                        digital_pot.set_rgb(digital_pot.value) # only on digital pot
#                   _motor_controller.set_speed(Orientation.ALL, _value)
                    _log.info('setting motor speeds ({:d}%)…'.format(round(_target_speed * 100)))
                    response = master.set_motor_speeds(_target_speed, _target_speed, _target_speed, _target_speed)
#                   _log.info(Fore.GREEN + 'response: {}'.format(response))

#                   if next(_counter) % 5 == 0:
#                       print('REQUEST STATUS...')
#                       response = master.request_status()
#                       _log.info(Fore.MAGENTA + 'status response: {}'.format(response))

                time.sleep(0.0667)

        else:

            _log.info('enabling (PING/ACK handshake)…')
            master.enable()

            # Test: Request status
            _log.info('requesting initial status…')
            response = master.request_status()
            _log.info(Fore.GREEN + 'status response: {}'.format(response))

            # Test: Set motor speeds
            _log.info('setting motor speeds (25%)…')
            response = master.set_motor_speeds(25.0, 25.0, 25.0, 25.0)
            _log.info(Fore.GREEN + 'response: {}'.format(response))
            time.sleep(0.05)

            # Test: Increase speed
            _log.info('setting motor speeds (50%)…')
            response = master.set_motor_speeds(50.0, 50.0, 50.0, 50.0)
            _log.info(Fore.GREEN + 'response: {}'.format(response))
            time.sleep(0.05)

            # Test: Stop motors
            _log.info('stopping motors…')
            response = master.stop_motors()
            _log.info(Fore.GREEN + 'response: {}'.format(response))

            # Test: Request final status
            _log.info('requesting final status…')
            response = master.request_status()
            _log.info(Fore.GREEN + 'status response: {}'.format(response))

            _log.info(Fore.GREEN + Style.BRIGHT + '\nall tests completed successfully!')

    except KeyboardInterrupt:
        _log.info('Ctrl-C caught; exiting…')
    except Exception as e:
        _log.error('{} raised during test: {}\n{}'.format(type(e), e, traceback.print_exc()))
    finally:
        if __IOE_AVAILABLE:
            if digital_pot:
                digital_pot.close()
        if master:
            _log.info(Fore.YELLOW + '\n8. Cleaning up...' + Style.RESET_ALL)
            master.disable()
            master.close()
            _log.info(Fore.CYAN + 'Done.' + Style.RESET_ALL)

if __name__ == '__main__':
    main()

#EOF
