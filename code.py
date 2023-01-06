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
OFFSET = config.OFFSET

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

# Tune Frequency
print("Measured Frequency: ", (sm.frequency + OFFSET)/1000)
sm.stop()
sm.frequency=(FREQ - sm.frequency) + FREQ
sm.restart()
print("Tuned To Configured Frequency: ", (sm.frequency + OFFSET)/1000)
sm.stop()

# setup buzzer (set duty cycle to ON to sound)
buzzer = pwmio.PWMOut(board.GP10,variable_frequency=True)
buzzer.frequency = SIDEFREQ
OFF = 0
ON = 2**15

# leds
txLED = digitalio.DigitalInOut(board.GP3)
txLED.direction = digitalio.Direction.OUTPUT
txLED.value = False

pwrLED = digitalio.DigitalInOut(board.GP4)
pwrLED.direction = digitalio.Direction.OUTPUT
pwrLED.value = True

loraLED = digitalio.DigitalInOut(board.GP5)
loraLED.direction = digitalio.Direction.OUTPUT
loraLED.value = True

def led(what):
    if what=='tx':
        txLED.value = True
        loraLED.value = False
        pwrLED.value = False
    if what=='txOFF':
        txLED.value = False
        loraLED.value = False
        pwrLED.value = True
    if what=='lora':
        txLED.value = False
        loraLED.value = True
        pwrLED.value = False
    if what=='loraOFF':
        txLED.value = False
        loraLED.value = False
        pwrLED.value = True

# setup usb serial
serial = usb_cdc.data

# setup encode and decode
encodings = {}
def encode(char):
    global encodings
    if char in encodings:
        return encodings[char]
    elif char.lower() in encodings:
        return encodings[char.lower()]
    else:
        return ''

decodings = {}
def decode(char):
    global decodings
    if char in decodings:
        return decodings[char]
    else:
        #return '('+char+'?)'
        return '¿'

def MAP(pattern,letter):
    decodings[pattern] = letter
    encodings[letter ] = pattern
    
MAP('.-'   ,'a') ; MAP('-...' ,'b') ; MAP('-.-.' ,'c') ; MAP('-..'  ,'d') ; MAP('.'    ,'e')
MAP('..-.' ,'f') ; MAP('--.'  ,'g') ; MAP('....' ,'h') ; MAP('..'   ,'i') ; MAP('.---' ,'j')
MAP('-.-'  ,'k') ; MAP('.-..' ,'l') ; MAP('--'   ,'m') ; MAP('-.'   ,'n') ; MAP('---'  ,'o')
MAP('.--.' ,'p') ; MAP('--.-' ,'q') ; MAP('.-.'  ,'r') ; MAP('...'  ,'s') ; MAP('-'    ,'t')
MAP('..-'  ,'u') ; MAP('...-' ,'v') ; MAP('.--'  ,'w') ; MAP('-..-' ,'x') ; MAP('-.--' ,'y')
MAP('--..' ,'z')
              
MAP('.----','1') ; MAP('..---','2') ; MAP('...--','3') ; MAP('....-','4') ; MAP('.....','5')
MAP('-....','6') ; MAP('--...','7') ; MAP('---..','8') ; MAP('----.','9') ; MAP('-----','0')

MAP('.-.-.-','.') # period
MAP('--..--',',') # comma
MAP('..--..','?') # question mark
MAP('-...-', '=') # equals, also /BT separator
MAP('-....-','-') # hyphen
MAP('-..-.', '/') # forward slash
MAP('.--.-.','@') # at sign

MAP('-.--.', '(') # /KN over to named station
MAP('.-.-.', '+') # /AR stop (end of message)
MAP('.-...', '&') # /AS wait
MAP('...-.-','|') # /SK end of contact
MAP('...-.', '*') # /SN understood
MAP('.......','#') # error

# key down and up
def cw(on):
    if on:
        # key.value = True
        led('tx')
        sm.restart()
        if SIDETONE:
           buzzer.duty_cycle = ON
    else:
        led('txOFF')
        sm.stop()
        # key.value = False
        buzzer.duty_cycle = OFF

# timing
def dit_time():
    global WPM
    PARIS = 50 
    return 60.0 / WPM / PARIS

# send to computer
def send(c):
#   print(c,end='')
    if serial.connected:
       serial.write(str.encode(c))
        
# transmit pattern
def play(pattern):
    for sound in pattern:
        if sound == '.':
            cw(True)
            time.sleep(dit_time())
            cw(False)
            time.sleep(dit_time())
        elif sound == '-':
            cw(True)
            time.sleep(3*dit_time())
            cw(False)
            time.sleep(dit_time())
        elif sound == ' ':
            time.sleep(4*dit_time())
    time.sleep(2*dit_time())

# receive, send, and play keystrokes from computer
def serials():
    if serial.connected:
        if serial.in_waiting > 0:
            letter = serial.read().decode('utf-8')
            send(letter)
            play(encode(letter))


# play beacon and pause            
def beacon():
    global cwBeacon
    letter = cwBeacon[:1]
    cwBeacon = cwBeacon[1:]
    send(letter)
    play(encode(letter))


# run
delay = " " * BEACONDELAY
cwBeacon = BEACON + delay
while True:
    if MODE is "SERIAL":
        serials()

    if MODE is "BEACON":
        beacon() 
        if len(cwBeacon) is 0:
            delay = " " * BEACONDELAY
            cwBeacon = BEACON + delay
        
