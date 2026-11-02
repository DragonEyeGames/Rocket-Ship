from machine import Pin, PWM
import time
from ms5611 import MS5611

# Use the exact pin we want to test
green = Pin(2, Pin.OUT)
red = Pin(28, Pin.OUT)
blue = Pin(17, Pin.OUT)
switch = Pin(0, Pin.IN, Pin.PULL_UP)

servo = PWM(Pin(15))
servo.freq(50)

cycles=0
backup_armed = 0

previous_alt = 1000000

i2c = machine.I2C(0, sda=machine.Pin(4), scl=machine.Pin(5), freq=400000)
print("Scanning I2C bus...")
devices = i2c.scan()

if devices:
    for device in devices:
        print(f"Found device at address: {hex(device)}")
else:
    print("No I2C devices found. Check your VCC/GND and SDA/SCL connections!")

sensor = MS5611(i2c, address=0x77)

def set_servo(angle):

    servo.duty_ns(int(angle))

def set_armed(armed_value):
    if armed_value == 0:
        green.value(1)
        red.value(0)
        blue.value(1)
        set_servo(1000000)
        print("armed")
    else:
        red.value(1)
        green.value(0)
        blue.value(1)
        set_servo(2000000)
        print("lax")

set_armed(switch.value())

while True:
    armed = switch.value()
    if(armed!=backup_armed):
        set_armed(armed)
    backup_armed=armed
    
    cycles = cycles+1
    if(cycles>=5):
        try:
            temp, press, alt = sensor.read_sensors()
            # Clean print format that outputs without cluttering your loop
            #print(f"Alt: {alt:.2f}m | Temp: {temp:.1f}°C")
            if(previous_alt!=1000000):
                print(f"Previous Alt: {previous_alt:.2f}m , New Alt: {alt:.2f}m")
            previous_alt=alt
        except OSError:
            print("Sensor error!")
        cycles=0
    
    time.sleep(.1)



