#!/usr/bin/env python3

import board
import busio
from adafruit_pca9685 import PCA9685
import lgpio

# ================= GPIO =================

M0_A, M0_B = 18, 17   # moteur gauche
M1_A, M1_B = 22, 27   # moteur droit

pins = [M0_A, M0_B, M1_A, M1_B]

gpio = lgpio.gpiochip_open(0)

for pin in pins:
    lgpio.gpio_claim_output(gpio, pin, 0)

# ================= PCA9685 =================

i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

pwm_left = pca.channels[5]
pwm_right = pca.channels[4]

pwm_left.duty_cycle = 0
pwm_right.duty_cycle = 0


# ================= FONCTIONS =================

def stop():
    pwm_left.duty_cycle = 0
    pwm_right.duty_cycle = 0
    for pin in pins:
        lgpio.gpio_write(gpio, pin, 0)
    print("STOP")


def motor_left(speed):

    duty = int(abs(speed) * 65535)

    if 0 < duty < 20000:
        duty = 20000

    pwm_left.duty_cycle = duty

    if speed > 0:
        lgpio.gpio_write(gpio, M0_A, 0)
        lgpio.gpio_write(gpio, M0_B, 1)
        print("Moteur gauche AVANT")

    elif speed < 0:
        lgpio.gpio_write(gpio, M0_A, 1)
        lgpio.gpio_write(gpio, M0_B, 0)
        print("Moteur gauche ARRIERE")

    else:
        pwm_left.duty_cycle = 0


def motor_right(speed):

    duty = int(abs(speed) * 65535)

    if 0 < duty < 20000:
        duty = 20000

    pwm_right.duty_cycle = duty

    if speed > 0:
        lgpio.gpio_write(gpio, M1_A, 0)
        lgpio.gpio_write(gpio, M1_B, 1)
        print("Moteur droit AVANT")

    elif speed < 0:
        lgpio.gpio_write(gpio, M1_A, 1)
        lgpio.gpio_write(gpio, M1_B, 0)
        print("Moteur droit ARRIERE")

    else:
        pwm_right.duty_cycle = 0


# ================= MENU TEST =================

def main():

    print("\n===== TEST MOTEURS ROBOT =====\n")

    print("1 : moteur gauche avant")
    print("2 : moteur gauche arrière")
    print("3 : moteur droit avant")
    print("4 : moteur droit arrière")
    print("5 : stop")
    print("q : quitter")

    while True:

        cmd = input("\nCommande : ")

        if cmd == "1":
            motor_left(0.5)

        elif cmd == "2":
            motor_left(-0.5)

        elif cmd == "3":
            motor_right(0.5)

        elif cmd == "4":
            motor_right(-0.5)

        elif cmd == "5":
            stop()

        elif cmd == "q":
            break

        else:
            print("Commande inconnue")

    stop()
    lgpio.gpiochip_close(gpio)
    print("Programme terminé")


if __name__ == "__main__":
    main()
