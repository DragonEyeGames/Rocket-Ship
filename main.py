from machine import Pin, PWM
import time
from ms5611 import MS5611
import os

# Get the info for the LED
green = Pin(2, Pin.OUT)
red = Pin(28, Pin.OUT)
blue = Pin(17, Pin.OUT)

# Get the info for the armed switch
switch = Pin(0, Pin.IN, Pin.PULL_UP)

# Get and initialize the servo
servo = PWM(Pin(15))
servo.freq(50)

cycles = 0
backup_armed = 0
armed_time = 0
armedCount = 0

previous_alts = []
previous_alt = 1000000

file_index = 1


def set_servo(angle):
    servo.duty_ns(int(angle))


def set_armed(armed_value):
    if armed_value:
        green.value(1)
        red.value(0)
        blue.value(1)
        set_servo(1000000)
        print("armed")
        armed_time = 0
    else:
        red.value(1)
        green.value(0)
        blue.value(1)
        set_servo(2000000)
        print("lax")
        armed_time = 0


def deployChute():
    red.value(1)
    green.value(1)
    blue.value(0)
    set_servo(2000000)


def average(list):
    total = 0
    items = 0
    for item in list:
        items += 1
        total += item
    return (total / items)


while f"flight_data_{file_index}.csv" in os.listdir():
    file_index += 1

FILENAME = f"flight_data_{file_index}.csv"

with open(FILENAME, "w") as f:
    f.write("Timestamp_ms,Altitude_m\n")
    print(f"Started fresh log file: {FILENAME}")

i2c = machine.I2C(0, sda=machine.Pin(4), scl=machine.Pin(5), freq=400000)
print("Scanning I2C bus...")
devices = i2c.scan()

if devices:
    for device in devices:
        print(f"Found device at address: {hex(device)}")
else:
    print("No I2C devices found. Check your VCC/GND and SDA/SCL connections!")

sensor = MS5611(i2c, address=0x77)

set_armed(switch.value() == 0)

while True:
    armed = (switch.value() == 0)
    if (armed != backup_armed):
        set_armed(armed)
    backup_armed = armed

    cycles = cycles + 1
    if (cycles >= 2 and armed):
        try:
            temp, press, alt = sensor.read_sensors()

            highest_alt = 0

            if (len(previous_alts) != 0):
                highest_alt = average(previous_alts)
                print(f"Previous Alt: {highest_alt:.2f}m , New Alt: {alt:.2f}m")

            previous_alts.append(alt)
            if (len(previous_alts) > 10):
                previous_alts.pop(0)

            if (alt < highest_alt - .5):
                armedCount += 1
                if (armedCount >= 3):
                    deployChute()
            else:
                armedCount = 0
            armed_time += .2
            with open(FILENAME, "a") as f:
                # Format as comma-separated values ending in a newline
                f.write(f"{armed_time},{alt:.2f}\n")
            print(f"Logged: {armed_time},{alt:.2f}")

        except OSError:
            print("Sensor error!")
        cycles = 0

    time.sleep(.1)
