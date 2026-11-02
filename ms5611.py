import machine
import time
import ustruct

class MS5611:
    def __init__(self, i2c, address=0x77):
        self.i2c = i2c
        self.address = address
        self.reset()
        time.sleep(0.1)
        self.read_prom()

    def reset(self):
        self.i2c.writeto(self.address, b'\x1E')

    def read_prom(self):
        self.C = []
        for i in range(6):
            reg = 0xA2 + (i * 2)
            data = self.i2c.readfrom_mem(self.address, reg, 2)
            val = ustruct.unpack('>H', data)[0]
            self.C.append(val)

    def read_raw_pressure(self):
        self.i2c.writeto(self.address, b'\x48')
        time.sleep(0.01)
        data = self.i2c.readfrom_mem(self.address, 0x00, 3)
        return (data[0] << 16) | (data[1] << 8) | data[2]

    def read_raw_temperature(self):
        self.i2c.writeto(self.address, b'\x58')
        time.sleep(0.01)
        data = self.i2c.readfrom_mem(self.address, 0x00, 3)
        return (data[0] << 16) | (data[1] << 8) | data[2]

    def read_sensors(self):
        D1 = self.read_raw_pressure()
        D2 = self.read_raw_temperature()

        dT = D2 - (self.C[4] * 256)
        TEMP = 2000 + int(dT * self.C[5] / 8388608)

        OFF = (self.C[1] * 65536) + int((self.C[3] * dT) / 128)
        SENS = (self.C[0] * 32768) + int((self.C[2] * dT) / 256)

        if TEMP < 2000:
            T2 = int((dT * dT) / 2147483648)
            OFF2 = int(5 * ((TEMP - 2000) ** 2) / 2)
            SENS2 = int(5 * ((TEMP - 2000) ** 2) / 4)
            if TEMP < -1500:
                OFF2 = OFF2 + int(7 * ((TEMP + 1500) ** 2))
                SENS2 = SENS2 + int(11 * ((TEMP + 1500) ** 2) / 2)
            TEMP -= T2
            OFF -= OFF2
            SENS -= SENS2

        P = int((((D1 * SENS) / 2097152) - OFF) / 32768)

        temp_c = TEMP / 100.0
        pressure_hpa = P / 100.0
        altitude_m = 44330.0 * (1.0 - (pressure_hpa / 1013.25) ** 0.1903)

        return temp_c, pressure_hpa, altitude_m

