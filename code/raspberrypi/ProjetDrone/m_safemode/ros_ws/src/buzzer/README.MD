# buzzer — Script de surveillance sonore

Script Python surveillant le topic ROS 2 `/robot_mode`.  
Lorsque le mode passe à `3` (safemode), le buzzer s'active pour alerter l'opérateur d'une perte de communication ou d'une défaillance système.

---

## Fonctionnement

```
/robot_mode ────────────► buzzer.py ────────────► Buzzer (GPIO)
  value = "3"                                       BIP actif
  value != "3"                                      silence
```

### Pipeline

1. **Abonnement** au topic `/robot_mode`
2. **Lecture de la valeur** à chaque message reçu
3. **Si valeur = `"3"`** — activation du buzzer via GPIO
4. **Sinon** — buzzer éteint, système nominal

---

## Topics

| Topic | Type | Rôle |
|---|---|---|
| `/robot_mode` | `std_msgs/String` | **Entrée** — mode actif du robot |

### Valeurs de `/robot_mode`

| Valeur | Signification | Buzzer |
|---|---|---|
| `"1"` | Mode manuel | Éteint |
| `"2"` | Mode verrouillage | Éteint |
| `"3"` | Safemode — urgence | **Actif** |

---

## Prérequis

- Python 3.8+
- ROS 2 Humble (ou supérieur) — pour la réception du topic
- Bibliothèque `RPi.GPIO` (Raspberry Pi)
- Buzzer connecté sur la broche GPIO correspondante

```bash
pip install RPi.GPIO
```

---

## Lancement

```bash
# Sourcer ROS 2
source /opt/ros/humble/setup.bash

# Lancer le script
python3 buzzer.py
```

---

## Tester le script manuellement

### Déclencher le buzzer (passer en safemode)

```bash
ros2 topic pub /robot_mode std_msgs/String "data: '3'"
```

> **Résultat attendu :** le buzzer s'active

### Désactiver le buzzer (retour mode nominal)

```bash
ros2 topic pub /robot_mode std_msgs/String "data: '1'"
```

> **Résultat attendu :** le buzzer s'éteint

### Vérifier que le topic est bien reçu

```bash
ros2 topic echo /robot_mode
```

---

## Structure du code

```
buzzer.py
├── BuzzerNode(Node)
│   ├── __init__()           # Subscriber /robot_mode, init GPIO
│   └── mode_callback()      # Active/désactive le buzzer selon la valeur
└── main()                   # Point d'entrée
```

---

## Comportements

| Situation | Comportement |
|---|---|
| `robot_mode = "3"` | Buzzer actif — alerte sonore |
| `robot_mode != "3"` | Buzzer éteint |
| Script arrêté brutalement | GPIO nettoyé — buzzer éteint |

---

## Auteur

**Nolan RIBETTE** — BTS CIEL IR · Drone cible d'entraînement pour la marine nationale · 2026
