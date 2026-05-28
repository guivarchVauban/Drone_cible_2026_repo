# 🎯 navigation_verrou — Nœud ROS 2 de suivi de cible

Nœud ROS 2 assurant le **suivi automatique d'un bateau** détecté par YOLOv5.  
Lorsque le mode verrouillage est actif (`robot_mode = 2`), le drone centre en continu la cible dans son champ de vision et avance vers elle.

---

## Fonctionnement

```
boat_detector        NavigationNode       robot_controller
     │                     │                     │
     │─/boat_detection_json►│                     │
     │                     │────/cmd_vel─────────►│
/robot_mode ────────────►  │
```

### Pipeline

1. **Abonnement** au topic `/boat_detection_json` — reçoit les coordonnées de la bounding box publiées par `boat_detector` (YOLOv5)
2. **Vérification du mode** — si `robot_mode ≠ 2`, aucune commande n'est envoyée (sécurité)
3. **Calcul de l'erreur** — écart en pixels entre le centre horizontal du bateau et le centre de l'image (320 px)
4. **Correcteur proportionnel (P)** — applique une vitesse angulaire proportionnelle à l'erreur pour corriger la direction
5. **Publication** sur `/cmd_vel` (type `geometry_msgs/Twist`)

### Loi de commande

| Paramètre | Valeur | Description |
|---|---|---|
| `linear.x` | `0.6` m/s | Vitesse d'avance constante vers la cible |
| `angular.z` | `-Kp * error` | Correction angulaire (gouvernail) |
| `Kp` | `0.002` | Gain proportionnel |
| `dead_zone` | `20 px` | Zone morte — évite les oscillations si cible déjà centrée |

---

## Topics

| Topic | Type | Role |
|---|---|---|
| `/boat_detection_json` | `std_msgs/String` | **Entrée** — coordonnées JSON de la bounding box |
| `/robot_mode` | `std_msgs/String` | **Entrée** — mode actif (`"2"` = verrouillage) |
| `/cmd_vel` | `geometry_msgs/Twist` | **Sortie** — commande moteurs/gouvernail |

### Format du JSON attendu sur `/boat_detection_json`

```json
{
  "boats": [
    {
      "x_min": 280.0,
      "width": 80.0,
      "height": 60.0,
      "confidence": 0.87
    }
  ]
}
```

---

## Prérequis

- ROS 2 Humble (ou supérieur)
- Python 3.8+
- Package `geometry_msgs`
- Nœud `boat_detector` actif (publie sur `/boat_detection_json`)
- `robot_mode` publié à `"2"` pour activer le suivi

---

## Lancement

### 1. Directement avec `ros2 run`

```bash
# Sourcer ROS 2
source /opt/ros/humble/setup.bash

# Sourcer le workspace du projet
source ~/ros2_ws/install/setup.bash

# Lancer le nœud
ros2 run drone_cible navigation_verrou
```

### 2. Avec le docker-compose du projet

```bash
docker-compose up navigation_verrou
```

---

## Tester le nœud manuellement

### Activer le mode verrouillage

```bash
ros2 topic pub /robot_mode std_msgs/String "data: '2'"
```

### Simuler une détection (bateau légèrement à droite)

```bash
ros2 topic pub /boat_detection_json std_msgs/String \
  "data: '{\"boats\": [{\"x_min\": 360.0, \"width\": 80.0, \"height\": 60.0, \"confidence\": 0.9}]}'"
```

### Vérifier les commandes publiées

```bash
ros2 topic echo /cmd_vel
```

> **Résultat attendu :** `linear.x = 0.6`, `angular.z < 0` (correction vers la droite)

### Désactiver le suivi

```bash
ros2 topic pub /robot_mode std_msgs/String "data: '3'"
```

> **Résultat attendu :** `linear.x = 0`, `angular.z = 0`

---

## Structure du code

```
navigation_verrou.py
├── NavigationNode(Node)
│   ├── __init__()              # Subscribers, publisher, timer 20 Hz
│   ├── mode_callback()         # Mise à jour du robot_mode
│   ├── detection_callback()    # Réception et parsing du JSON YOLOv5
│   └── control_loop()          # Calcul et publication sur /cmd_vel
└── main()                      # Point d'entrée ROS 2
```

---

## Comportements de sécurité

| Situation | Comportement |
|---|---|
| `robot_mode != 2` | Aucune commande publiée — drone immobile |
| Aucune détection reçue | Aucune commande publiée — drone immobile |
| Erreur `< 20 px` (zone morte) | `angular.z = 0` — pas de correction angulaire |
| Nœud arrêté brutalement | `/cmd_vel` cesse d'être publié — `robot_controller` stoppe les moteurs |

---

## Auteur

**Nolan RIBETTE** — BTS CIEL IR · Drone cible d'entraînement pour la marine nationale · 2026
