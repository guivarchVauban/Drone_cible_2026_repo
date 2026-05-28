from gpiozero import Buzzer
import time

buzzer = Buzzer(23)

# Erika — notes représentées par durées (on/off)
# Format : (duree_on, duree_off)
# Courte = croche, longue = noire, très longue = blanche

COURT = 0.15
MOYEN = 0.30
LONG  = 0.45
PAUSE = 0.08

erika = [
    # "Auf der Heide blüht ein kleines Blümelein"
    (MOYEN, PAUSE),
    (COURT, PAUSE),
    (MOYEN, PAUSE),
    (LONG,  PAUSE),
    (COURT, PAUSE),
    (COURT, PAUSE),
    (MOYEN, PAUSE),
    (LONG,  0.20),

    (MOYEN, PAUSE),
    (COURT, PAUSE),
    (MOYEN, PAUSE),
    (LONG,  PAUSE),
    (COURT, PAUSE),
    (COURT, PAUSE),
    (LONG,  0.30),

    # "und das heißt Erika"
    (COURT, PAUSE),
    (COURT, PAUSE),
    (COURT, PAUSE),
    (MOYEN, PAUSE),
    (COURT, PAUSE),
    (LONG,  0.25),

    (COURT, PAUSE),
    (COURT, PAUSE),
    (COURT, PAUSE),
    (MOYEN, PAUSE),
    (COURT, PAUSE),
    (LONG,  0.40),

    # "Heiß von Träumen..."
    (MOYEN, PAUSE),
    (COURT, PAUSE),
    (MOYEN, PAUSE),
    (LONG,  PAUSE),
    (COURT, PAUSE),
    (COURT, PAUSE),
    (MOYEN, PAUSE),
    (LONG,  0.20),

    (MOYEN, PAUSE),
    (COURT, PAUSE),
    (MOYEN, PAUSE),
    (LONG,  PAUSE),
    (COURT, PAUSE),
    (COURT, PAUSE),
    (LONG,  0.30),

    # "In der Heimat..."
    (COURT, PAUSE),
    (COURT, PAUSE),
    (COURT, PAUSE),
    (MOYEN, PAUSE),
    (COURT, PAUSE),
    (MOYEN, PAUSE),
    (COURT, PAUSE),
    (LONG,  0.25),

    (COURT, PAUSE),
    (COURT, PAUSE),
    (COURT, PAUSE),
    (MOYEN, PAUSE),
    (COURT, PAUSE),
    (LONG,  0.50),
]

print("🎵 Erika — début")
try:
    for duree_on, duree_off in erika:
        buzzer.on()
        time.sleep(duree_on)
        buzzer.off()
        time.sleep(duree_off)
    print("🎵 Fin")
except KeyboardInterrupt:
    print("Interrompu")
finally:
    buzzer.off()
