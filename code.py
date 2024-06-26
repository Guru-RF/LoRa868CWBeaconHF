# LoraCWBeacon Copyright 2023 Joeri Van Dooren (ON3URE)

import asyncio
import random
import time

import adafruit_rfm9x
import adafruit_si5351
import board
import busio
import digitalio
from adafruit_datetime import datetime

import config


# User config
WPM = config.WPM
FREQ = config.FREQ
BEACON = config.BEACON
BEACONDELAY = config.BEACONDELAY

# Create the I2C interface.
XTAL_FREQ = 25000000
i2c = busio.I2C(scl=board.GP27, sda=board.GP26)
si5351 = adafruit_si5351.SI5351(i2c)

# leds
pwrLED = digitalio.DigitalInOut(board.GP9)
pwrLED.direction = digitalio.Direction.OUTPUT
pwrLED.value = True

txLED = digitalio.DigitalInOut(board.GP10)
txLED.direction = digitalio.Direction.OUTPUT
txLED.value = False

loraLED = digitalio.DigitalInOut(board.GP11)
loraLED.direction = digitalio.Direction.OUTPUT
loraLED.value = False


def setFrequency(frequency):
    xtalFreq = XTAL_FREQ
    divider = int(900000000 / frequency)
    if divider % 2:
        divider -= 1
    pllFreq = divider * frequency
    mult = int(pllFreq / xtalFreq)
    l = int(pllFreq % xtalFreq)
    f = l
    f *= 1048575
    f /= xtalFreq
    num = int(f)
    denom = 1048575
    si5351.pll_a.configure_fractional(mult, num, denom)
    si5351.clock_0.configure_integer(si5351.pll_a, divider)


def led(what):
    if what == "tx":
        txLED.value = True
    if what == "txOFF":
        txLED.value = False
    if what == "lora":
        loraLED.value = True
    if what == "loraOFF":
        loraLED.value = False


# setup encode and decode
encodings = {}


def encode(char):
    global encodings
    if char in encodings:
        return encodings[char]
    elif char.lower() in encodings:
        return encodings[char.lower()]
    else:
        return ""


decodings = {}


def decode(char):
    global decodings
    if char in decodings:
        return decodings[char]
    else:
        # return '('+char+'?)'
        return "¿"


def MAP(pattern, letter):
    decodings[pattern] = letter
    encodings[letter] = pattern


MAP(".-", "a")
MAP("-...", "b")
MAP("-.-.", "c")
MAP("-..", "d")
MAP(".", "e")
MAP("..-.", "f")
MAP("--.", "g")
MAP("....", "h")
MAP("..", "i")
MAP(".---", "j")
MAP("-.-", "k")
MAP(".-..", "l")
MAP("--", "m")
MAP("-.", "n")
MAP("---", "o")
MAP(".--.", "p")
MAP("--.-", "q")
MAP(".-.", "r")
MAP("...", "s")
MAP("-", "t")
MAP("..-", "u")
MAP("...-", "v")
MAP(".--", "w")
MAP("-..-", "x")
MAP("-.--", "y")
MAP("--..", "z")

MAP(".----", "1")
MAP("..---", "2")
MAP("...--", "3")
MAP("....-", "4")
MAP(".....", "5")
MAP("-....", "6")
MAP("--...", "7")
MAP("---..", "8")
MAP("----.", "9")
MAP("-----", "0")

MAP(".-.-.-", ".")  # period
MAP("--..--", ",")  # comma
MAP("..--..", "?")  # question mark
MAP("-...-", "=")  # equals, also /BT separator
MAP("-....-", "-")  # hyphen
MAP("-..-.", "/")  # forward slash
MAP(".--.-.", "@")  # at sign

MAP("-.--.", "(")  # /KN over to named station
MAP(".-.-.", "+")  # /AR stop (end of message)
MAP(".-...", "&")  # /AS wait
MAP("...-.-", "|")  # /SK end of contact
MAP("...-.", "*")  # /SN understood
MAP(".......", "#")  # error


# key down and up
def cw(on):
    if on:
        led("tx")
        si5351.outputs_enabled = True
    else:
        led("txOFF")
        si5351.outputs_enabled = False


# timing
def dit_time():
    global WPM
    PARIS = 50
    return 60.0 / WPM / PARIS


# transmit pattern
def play(pattern):
    for sound in pattern:
        if sound == ".":
            cw(True)
            time.sleep(dit_time())
            cw(False)
            time.sleep(dit_time())
        elif sound == "-":
            cw(True)
            time.sleep(3 * dit_time())
            cw(False)
            time.sleep(dit_time())
        elif sound == " ":
            time.sleep(4 * dit_time())
    time.sleep(2 * dit_time())


# play beacon and pause
def beacon():
    global cwBeacon
    letter = cwBeacon[:1]
    cwBeacon = cwBeacon[1:]
    print(letter, end="")
    play(encode(letter))


async def loraLoop(loop):
    # LoRa APRS frequency
    RADIO_FREQ_MHZ = 868.000
    CS = digitalio.DigitalInOut(board.GP21)
    RESET = digitalio.DigitalInOut(board.GP20)
    spi = busio.SPI(board.GP18, MOSI=board.GP19, MISO=board.GP16)
    rfm9x = adafruit_rfm9x.RFM9x(
        spi, CS, RESET, RADIO_FREQ_MHZ, baudrate=1000000, agc=False, crc=True
    )

    while True:
        await asyncio.sleep(5)
        stamp = datetime.now()
        timeout = int(config.LORATIMEOUT) + random.randint(1, 9)

        print(
            f"{stamp}: [{config.CALL}] loraRunner: Waiting for lora APRS packet ...\r",
            end="",
        )
        packet = await rfm9x.areceive(with_header=True, timeout=timeout)
        if packet is not None:
            if packet[:3] == (b"<\xaa\x01"):
                try:
                    rawdata = bytes(packet[3:]).decode("utf-8")
                    stamp = datetime.now()
                    print(
                        f"\r{stamp}: [{config.CALL}] loraRunner: RSSI:{rfm9x.last_rssi} Data:{rawdata}"
                    )
                except:
                    print(
                        f"{stamp}: [{config.CALL}] loraRunner: Lost Packet, unable to decode, skipping"
                    )
                    continue


async def beaconLoop():
    global cwBeacon
    global BEACON
    global FREQ
    cwBeacon = BEACON
    setFrequency(FREQ * 1000)
    print("Measured Frequency: {0:0.3f} MHz".format(si5351.clock_0.frequency / 1000000))
    while True:
        beacon()
        await asyncio.sleep(0)
        if len(cwBeacon) == 0:
            cwBeacon = BEACON
            await asyncio.sleep(BEACONDELAY)


async def main():
    loop = asyncio.get_event_loop()
    loraL = asyncio.create_task(loraLoop(loop))
    cwL = asyncio.create_task(beaconLoop())
    await asyncio.gather(cwL, loraL)


asyncio.run(main())
