import time
import ustruct

class MS5611:
    def __init__(self, i2c, address=0x77):
        self.i2c = i2c
        self.address = address
        self.reset()
        time.sleep(0.1)
        self.read_prom()
        self.update_temp()

    def reset(self):
        self.i2c.writeto(self.address, b'\x1E')

    def read_prom(self):
        self.C = []
        for i in range(6):
            data = self.i2c.readfrom_mem(self.address, 0xA2 + i * 2, 2)
            self.C.append(ustruct.unpack('>H', data)[0])

    def _read_raw(self, cmd):
        self.i2c.writeto(self.address, cmd)
        time.sleep(0.003)
        data = self.i2c.readfrom_mem(self.address, 0x00, 3)
        return (data[0] << 16) | (data[1] << 8) | data[2]

    def update_temp(self):
        # Call this once at startup (and again before arming if you like)
        C = self.C
        D2 = self._read_raw(b'\x54')
        dT = D2 - C[4] * 256
        TEMP = 2000 + (dT * C[5]) // 8388608
        OFF = C[1] * 65536 + (C[3] * dT) // 128
        SENS = C[0] * 32768 + (C[2] * dT) // 256

        if TEMP < 2000:
            d = TEMP - 2000
            T2 = (dT * dT) // 2147483648
            OFF2 = (5 * d * d) // 2
            SENS2 = (5 * d * d) // 4
            if TEMP < -1500:
                e = TEMP + 1500
                OFF2 += 7 * e * e
                SENS2 += (11 * e * e) // 2
            OFF -= OFF2
            SENS -= SENS2

        self._OFF = OFF
        self._SENS = SENS

    def read_sensors(self):
        # Altitude only: one pressure conversion per call
        D1 = self._read_raw(b'\x44')
        P = ((D1 * self._SENS) // 2097152 - self._OFF) // 32768
        return 44330.0 * (1.0 - ((P / 100.0) / 1013.25) ** 0.1903)
