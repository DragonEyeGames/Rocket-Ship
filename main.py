from machine import Pin, PWM
import time

# Use the exact pin we want to test
green = Pin(2, Pin.OUT)
red = Pin(28, Pin.OUT)
switch = Pin(0, Pin.IN, Pin.PULL_UP)

servo = PWM(Pin(16))
servo.freq(50)

def set_servo(angle):
    # Maps 0 degrees to 1,000,000 ns (1ms)
    # Maps 180 degrees to 2,000,000 ns (2ms)
    pulse = 1000000 + (angle / 180) * 1000000
    servo.duty_ns(int(pulse))

while True:
    armed = switch.value()
    if armed == 0:
        green.value(1)
        red.value(0)
        set_servo(0)      # Sends 1,000,000 ns
    else:
        red.value(1)
        green.value(0)
        set_servo(180)    # Sends 2,000,000 ns
    time.sleep(.1)
