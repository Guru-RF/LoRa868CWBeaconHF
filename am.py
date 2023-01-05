# LoraCWBeacon Copyright 2023 Joeri Van Dooren (ON3URE)

# based on xiaoKey

# xiaoKey - a computer connected iambic keyer
# Copyright 2022 Mark Woodworth (AC9YW)
# https://github.com/MarkWoodworth/xiaokey/blob/master/code/code.py

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import time
import board
import digitalio
import pwmio
from digitalio import DigitalInOut, Direction, Pull
import usb_cdc
import rp2pio
import adafruit_pioasm
import config

# User config
WPM = config.WPM
SIDETONE = config.SIDETONE
SIDEFREQ = config.SIDEFREQ
FREQ = config.FREQ
BEACON = config.BEACON
MODE = config.MODE
BEACONDELAY = config.BEACONDELAY

# Vars
KEYBOARD = False

# PIO
osc = """
.program osc
    set pins 1 [1] 
    set pins 0 [1]  
"""

assembled = adafruit_pioasm.assemble(osc)

sm = rp2pio.StateMachine(
    assembled,
    frequency=FREQ,
    init=adafruit_pioasm.assemble("set pindirs 1"),
    first_set_pin=board.GP16,
)

print("real frequency: ", sm.frequency)
sm.stop()

counter = 0
state = 0
while True:
    time.sleep(0.03)
    if counter < 1000:
        if state is 1:
            sm.restart()
            state = 0
        else:
            sm.stop()
            state = 1
    else:
        if (counter > 2000):
            sm.restart()
        else:
            counter = 0

    counter = counter +1