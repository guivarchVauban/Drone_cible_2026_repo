from gpiozero import Buzzer
import time

buzzer = Buzzer(23)

C = 0.18
L = 0.36
P = 0.08
R = 0.25  # pause entre phrases

def bip(duree):
    buzzer.on()
    time.sleep(duree)
    buzzer.off()
    time.sleep(P)

def pause(duree=R):
    time.sleep(duree)

print("🦈 Baby Shark — début")
try:
    # "Baby shark, doo doo doo doo doo doo"
    for _ in range(3):
        bip(L)   # Ba-
        bip(C)   # by
        bip(C)   # shark
        pause(0.1)
        bip(C)   # doo
        bip(C)   # doo
        bip(C)   # doo
        bip(C)   # doo
        bip(C)   # doo
        bip(C)   # doo
        pause()

    bip(L)       # Ba-
    bip(C)       # by
    bip(L)       # shaaark
    pause(0.4)

    # "Mommy shark"
    for _ in range(3):
        bip(L)
        bip(C)
        bip(C)
        pause(0.1)
        bip(C)
        bip(C)
        bip(C)
        bip(C)
        bip(C)
        bip(C)
        pause()

    bip(L)
    bip(C)
    bip(L)
    pause(0.4)

    # "Daddy shark"
    for _ in range(3):
        bip(L)
        bip(C)
        bip(C)
        pause(0.1)
        bip(C)
        bip(C)
        bip(C)
        bip(C)
        bip(C)
        bip(C)
        pause()

    bip(L)
    bip(C)
    bip(L)
    pause(0.4)

    # "Do do do do do do" final rapide
    for _ in range(6):
        bip(0.10)

    bip(L)
    print("🦈 Fin !")

except KeyboardInterrupt:
    print("Interrompu")
finally:
    buzzer.off()
EOF
