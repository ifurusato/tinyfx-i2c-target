***********************************************************
tinyfx-i2c-target: The Pimoroni TinyFX as an I2C Peripheral
***********************************************************

Description
***********

Installing this library on a Pimoroni TinyFX permits it to be used as an I2C
target|slave, i.e., it can be controlled remotely from an I2C controller|master 
such as a Raspberry Pi. Any microcontroller could also be used, but the master's 
I2C implementation (smbus) would need to be replaced.


Usage
*****

Execute the tinyfx_ctrl.py file to display its command line, from where you
can type commands::

    ch[1-6] on|off        # control channels
    all on|off            # turn all channels on or off (including RGB LED)
    heartbeat on|off      # blinking RGB LED
    color [name]          # set RGB LED to color name (see colors.py)
    play [sound-name]     # play a sound (a *.wav file in sounds directory)

Examples include::

    ch2 on
    ch3 off
    all off
    heartbeat on
    color violet
    play beep

Setting the heartbeat or color will disable the other.

The distribution includes two sound files, beep and arming-tone. The latter
is automatically played with the TinyFX starts up (if it has a connected
speaker, of course). If you don't want this to occur, comment out the line
in the constructor.

The PIR sensor functionality currently is not working/has not been tested.


Requirements
************

This requires Python 3 on the master, and a Pimoroni MicroPython build supporting
I2CTarget such as "tiny_fx-2a5a3aaeb5cd7114ec6657611e2edaed25fc5664-micropython"
as found at: https://github.com/pimoroni/picofx/actions/runs/19371986148

Installation on the TinyFX is relatively simple: hold down the BOOT button, then
press RST and release, then release BOOT. This will cause the TinyFX to be mounted
to your computer. You can then copy or drag-and-drop the distribution file directly 
onto the mounted drive. It will then reset and update the firmware. You will then
be able to confirm the installation from the Python REPL::

    /pyboard> repl
    Entering REPL. Use Control-X to exit.
    >
    MicroPython v1.26.1 on 2025-11-14; Pimoroni TinyFX with RP2040
    Type "help()" for more information.

You should see the "MicroPython v1.26.1 on 2025-11-14; Pimoroni TinyFX with RP2040"
identifier, or a suitable update from Pimoroni.


Status
******

* 2025-11-17: first public release


Support & Liability
*******************

This project comes with no promise of support or acceptance of liability. Use at
your own risk.


Copyright & License
*******************

All contents (including software, documentation and images) Copyright 2020-2025
by Ichiro Furusato. All rights reserved.

Software and documentation are distributed under the MIT License, see LICENSE
file included with project.

