from gpiozero import Buzzer
import time
import threading

BUZZER_PIN = 23

buzzer = Buzzer(BUZZER_PIN)
_stop_event = threading.Event()

def sirene():
    _stop_event.clear()
    print("🚨 SIRÈNE ACTIVE — Ctrl+C pour stopper")

    try:
        while not _stop_event.is_set():
            # Montée — bips de plus en plus courts
            for duree in [0.35, 0.25, 0.15, 0.08, 0.05]:
                if _stop_event.is_set(): break
                buzzer.on()
                time.sleep(duree)
                buzzer.off()
                time.sleep(0.03)

            if _stop_event.is_set(): break

            # Descente — bips de plus en plus longs
            for duree in [0.05, 0.08, 0.15, 0.25, 0.35]:
                if _stop_event.is_set(): break
                buzzer.on()
                time.sleep(duree)
                buzzer.off()
                time.sleep(0.03)

    finally:
        buzzer.off()
        print("✅ Sirène arrêtée")

def stopper_sirene():
    _stop_event.set()
    buzzer.off()

def sirene_en_thread():
    t = threading.Thread(target=sirene, daemon=True)
    t.start()
    return t

if __name__ == "__main__":
    try:
        sirene()
    except KeyboardInterrupt:
        stopper_sirene()
        print("Programme terminé")
