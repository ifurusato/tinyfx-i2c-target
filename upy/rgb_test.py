
import utime
from tiny_fx import TinyFX
from picofx import MonoPlayer, ColourPlayer

from picofx.mono import RandomFX, StaticFX, BlinkFX
from i2c_settable_blink import I2CSettableBlinkFX
from settable import SettableFX

# ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

tiny = TinyFX()                         # create a new TinyFX object to interact with the board
player = MonoPlayer(tiny.outputs)       # create a new effect player to control TinyFX's mono outputs
rgb_player = ColourPlayer(tiny.rgb)     # create a new effect player to control TinyFX's RGB output

# set up the effects to play

_settable1 = SettableFX(brightness=0.5)
_settable2 = SettableFX(brightness=0.5)
_settable3 = SettableFX(brightness=0.5)
_settable4 = SettableFX(brightness=0.5)
_settable5 = SettableFX(brightness=0.5)
_settable6 = SettableFX(brightness=0.5)

#   I2CSettableBlinkFX(1, speed=0.5, phase=0.0, duty=0.015),
player.effects = [
    _settable1,
    _settable2,
    _settable3,
    _settable4,
    _settable5,
    _settable6
]   

# wrap the code in a try block, to catch any exceptions (including KeyboardInterrupt)
try:
#   _settable2.toggle()

    player.start()   # start the effects running
    # loop until the effect stops or the "Boot" button is pressed
    while player.is_running() and not tiny.boot_pressed():
        _settable1.toggle()
        utime.sleep(0.334)
        _settable2.toggle()
        utime.sleep(0.334)
        _settable3.toggle()
        utime.sleep(0.334)
        _settable4.toggle()
        utime.sleep(0.334)
        _settable5.toggle()
        utime.sleep(0.334)
        _settable6.toggle()
        utime.sleep(0.334)

# stop any running effects and turn off all the outputs
finally:
    player.stop()
    tiny.shutdown()
    

