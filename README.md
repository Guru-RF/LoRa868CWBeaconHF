# LoraCWBeacon
Standaline CW beacon/transmitter, remote controllable via LORA

# Configuration
WPM => Words per minute
FREQ => Frequency in HZ
SIDETONE => If the internal piezo sidetone is active or not
SIDEFREQ => Frequency of the internal piezo sidetone
BEACON => Beacon Text
BEACONDELAY => Silence between BEACON TX
MODE => Beacon|Serial|Lora

# MODE Beacon
When the LoraCWBeacon is booted there is a serial port presented over USB-C ... you can read CW text transmitted by the beacon

# MODE Serial
When the LoraCWBeacon is booted there is a serial port presented over USB-C ... you can enter CW to be transmitted by the beacon

# MODE Lora
The beacon waits for LORA commands and acts on it ... (needs to be completed)
