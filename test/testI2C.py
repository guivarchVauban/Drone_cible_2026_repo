import smbus2

bus = smbus2.SMBus(1)
FXAS21002_ADDR = 0x1C

who_am_i = bus.read_byte_data(FXAS21002_ADDR, 0x0C)  # Reg WHO_AM_I
print(hex(who_am_i))
