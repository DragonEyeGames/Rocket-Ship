from machine import Pin, PWM
import time
from ms5611 import MS5611

# Use the exact pin we want to test
green = Pin(2, Pin.OUT)
red = Pin(28, Pin.OUT)
switch = Pin(0, Pin.IN, Pin.PULL_UP)

servo = PWM(Pin(15))
servo.freq(50)

backup_armed = 0

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

while True:
    armed = switch.value()
    if(armed!=backup_armed):
        if armed == 0:
            green.value(1)
            red.value(0)
            set_servo(1000000)
            print("armed")
        else:
            red.value(1)
            green.value(0)
            set_servo(2000000)
            print("lax")
    backup_armed=armed
    
    try:
        temp, press, alt = sensor.read_sensors()
        # Clean print format that outputs without cluttering your loop
        print(f"Alt: {alt:.2f}m | Temp: {temp:.1f}°C")
    except OSError:
        print("Sensor error!")
    
    time.sleep(.1)



