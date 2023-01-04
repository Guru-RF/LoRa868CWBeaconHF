import time
import rp2pio
import board
import adafruit_pioasm

osc = """
.program osc
    set pins 1 [1] 
    set pins 0 [1]  
"""

assembled = adafruit_pioasm.assemble(osc)

sm = rp2pio.StateMachine(
    assembled,
    frequency=7005250,
    init=adafruit_pioasm.assemble("set pindirs 1"),
    first_set_pin=board.GP16,
)
print("real frequency", sm.frequency)

while True:
    sm.stop()
    time.sleep(2)
    print('Beep')
    sm.restart()
    time.sleep(5)