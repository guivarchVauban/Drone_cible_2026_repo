#!/usr/bin/env python3
import smbus2
import time
import math

# --- Adresses I2C ---
FXOS8700_ADDR = 0x1F  # Accel + Mag
FXAS21002_ADDR = 0x21  # Gyro

# --- Bus I2C ---
bus = smbus2.SMBus(1)

# --- FXOS8700 Setup ---
bus.write_byte_data(FXOS8700_ADDR, 0x2A, 0x01)  # CTRL_REG1 -> mode actif
bus.write_byte_data(FXOS8700_ADDR, 0x2B, 0x00)  # CTRL_REG2 normal
bus.write_byte_data(FXOS8700_ADDR, 0x5B, 0x1F)  # M_CTRL_REG1 -> hybrid mode + oversample
bus.write_byte_data(FXOS8700_ADDR, 0x5C, 0x20)  # M_CTRL_REG2 -> auto-calibration

# --- FXAS21002 Setup ---
bus.write_byte_data(FXAS21002_ADDR, 0x13, 0x00)  # CTRL_REG1 -> standby
bus.write_byte_data(FXAS21002_ADDR, 0x13, 0x0E)  # CTRL_REG1 -> active mode 100Hz

# --- Fonction pour lire 16-bit signé ---
def read16(addr, reg):
    high = bus.read_byte_data(addr, reg)
    low = bus.read_byte_data(addr, reg+1)
    val = (high << 8) | low
    if val & 0x8000:
        val -= 65536
    return val

# --- Conversion ---
ACCEL_SCALE = 0.000244  # g/LSB pour ±2g
GYRO_SCALE = 0.0625     # °/s par LSB pour full scale ±2000 dps

try:
    while True:
        # --- Accéléromètre ---
        ax = read16(FXOS8700_ADDR, 0x01) * ACCEL_SCALE * 9.80665  # m/s²
        ay = read16(FXOS8700_ADDR, 0x03) * ACCEL_SCALE * 9.80665
        az = read16(FXOS8700_ADDR, 0x05) * ACCEL_SCALE * 9.80665

        # --- Magnétomètre ---
        mx = read16(FXOS8700_ADDR, 0x33)
        my = read16(FXOS8700_ADDR, 0x35)
        mz = read16(FXOS8700_ADDR, 0x37)

        # Calcul heading (yaw) en degrés
        heading_rad = math.atan2(my, mx)
        heading_deg = math.degrees(heading_rad)
        if heading_deg < 0:
            heading_deg += 360

        # --- Gyroscope ---
        gx = read16(FXAS21002_ADDR, 0x01) * GYRO_SCALE  # °/s
        gy = read16(FXAS21002_ADDR, 0x03) * GYRO_SCALE
        gz = read16(FXAS21002_ADDR, 0x05) * GYRO_SCALE

        # --- Affichage ---
        print(f"Accel: X={ax:.2f} Y={ay:.2f} Z={az:.2f} m/s²")
        print(f"Mag:   X={mx} Y={my} Z={mz} | Heading={heading_deg:.1f}°")
        print(f"Gyro:  X={gx:.2f} Y={gy:.2f} Z={gz:.2f} °/s")
        print("-"*50)
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Fin du programme")
