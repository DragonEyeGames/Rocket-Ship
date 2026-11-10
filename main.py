from machine import Pin, PWM, I2C
import time
from ms5611 import MS5611
import os
import gc

# The RGB and Switch Pins
green = Pin(27, Pin.OUT)
red = Pin(28, Pin.OUT)
blue = Pin(26, Pin.OUT)
switch = Pin(16, Pin.IN, Pin.PULL_UP)

last_tick = time.ticks_ms()
save_cycles = 0

# Servo
servo = PWM(Pin(15))
servo.freq(50)

cycles = 0
backup_armed = 0
armed_time = 0

previous_alts = []
file_index = 1
highest_alt = 0
armedCount = 0
establishingBaseline = True
baseline = 0

# Dynamic file logging
while f"flight_data_{file_index}.csv" in os.listdir():
    file_index += 1

FILENAME = f"flight_data_{file_index}.csv"

with open(FILENAME, "w") as f:
    f.write("Timestamp_ms,Altitude_m\n")
    print(f"Started fresh log file: {FILENAME}")

# I2C Configuration
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100000)
time.sleep_ms(200)  
print("Scanning I2C bus...")
devices = i2c.scan()

sensor = None
for attempt in range(5):
    try:
        # NOTE: Ensure your MS5611 library class initialization matches this layout
        sensor = MS5611(i2c, address=0x77)
        break
    except OSError:
        print("Baro init failed, retrying...", attempt)
        time.sleep_ms(200)

if sensor is None:
    print("Baro not responding!")

def set_servo(angle):
    servo.duty_ns(int(angle))

def set_armed(armed_value):
    global armed_time  # FIXED: Allows altering global variable without crashing
    if armed_value:
        green.value(1)
        red.value(0)
        blue.value(1)
        set_servo(1000000)
        print("Armed and Ready")
    else:
        red.value(1)
        green.value(0)
        blue.value(1)
        set_servo(2000000)
        print("Disarmed (Lax)")
    armed_time = 0

def deployChute():
    red.value(1)
    green.value(1)
    blue.value(0)
    set_servo(2000000)
    print("!!! CHUTE DEPLOYED !!!")

def average(lst):
    if not lst:
        return 0
    return sum(lst) / len(lst)

# Set initial arming state
set_armed(switch.value() == 0)
sitting_time = 0

print("Establishing baseline altitude (Keep rocket still)...")
while establishingBaseline:
    try:
        # Extract altitude. Note: If read_sensors() returns a tuple, grab index [0]
        reading = sensor.read_sensors()
        alt = reading[0] if isinstance(reading, (tuple, list)) else reading
        
        previous_alts.append(alt)
        
        # Keep the baseline list small to avoid memory allocation errors
        if len(previous_alts) > 10:
            previous_alts.pop(0)
            
    except OSError:
        print("Sensor read error during baseline setup")

    time_passed_ms = time.ticks_diff(time.ticks_ms(), last_tick)
    sitting_time += time_passed_ms
    last_tick = time.ticks_ms()
    time.sleep_ms(20)  # Yields CPU control
    
    if sitting_time > 5000:
        establishingBaseline = False
        # Calculate clean median baseline
        sorted_alts = sorted(previous_alts)
        current_baseline = sorted_alts[len(sorted_alts) // 2]
        
        previous_alts.clear()
        for i in range(6):
            previous_alts.append(current_baseline)
        highest_alt = current_baseline
        baseline = current_baseline

print(f"Baseline established at: {highest_alt:.2f}m. Ready for launch.")
gc.collect()

# Open file once globally to eliminate file buffer allocation crashes in flight loop
with open(FILENAME, "a") as log_file:
    while True:
        armed = (switch.value() == 0)
        if armed != backup_armed:
            set_armed(armed)
        backup_armed = armed
        
        if armed:
            try:
                reading = sensor.read_sensors()
                alt = reading[0] if isinstance(reading, (tuple, list)) else reading
                
                previous_alts.append(alt)
                if len(previous_alts) > 6:
                    previous_alts.pop(0)
                    
                alt_filtered = average(previous_alts)
                
                # Dynamically track the true apogee (highest altitude reached)
                if alt_filtered > highest_alt:
                    highest_alt = alt_filtered
                    print(highest_alt)
                
                if(highest_alt >baseline+2):
                    blue.value(0)
                    red.value(0)
                    green.value(1)
                
                    # Check for sustained 1-meter drop below apogee
                    if (alt_filtered < (highest_alt - 1.0)):
                        armedCount += 1
                        if armedCount >= 5:
                            deployChute()
                    else:
                        armedCount = 0
                else:
                    blue.value(1)
                    red.value(0)
                    green.value(1)
                
                # Update flight stopwatch timing
                time_passed_ms = time.ticks_diff(time.ticks_ms(), last_tick)
                armed_time += time_passed_ms
                last_tick = time.ticks_ms()
                
                save_cycles += 1
                if save_cycles >= 10:
                    log_file.write(f"{armed_time},{alt_filtered:.2f}\n")
                    log_file.flush()  # Forces save directly to flash without closing file
                    save_cycles = 0
                
            except OSError:
                print("Flight loop sensor error!")
                
            time.sleep_ms(15)




