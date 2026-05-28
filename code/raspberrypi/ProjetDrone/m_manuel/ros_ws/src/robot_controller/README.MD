# robot_controller_node

## Description

Ce nœud ROS 2 assure le **contrôle bas niveau du robot terrestre**. Il tourne sur la **Raspberry Pi embarquée** et traduit les commandes de mouvement ROS 2 en signaux physiques vers les moteurs DC et le servo de direction, via un PCA9685 (I2C) et les GPIO de la Raspberry Pi 5.

---

## Ce que fait le nœud

### Contrôle des moteurs DC (`set_motors`)

- Deux moteurs DC pilotés en PWM via le **PCA9685** (canaux 4 et 5)
- Le sens de rotation est contrôlé par les **GPIO** de la Raspberry Pi (broches 17, 18, 22, 27)
- La vitesse est issue de `linear.x` du message `Twist` reçu sur `/cmd_vel`
- Un seuil minimum de PWM (`20000 / 65535`) est appliqué pour garantir le démarrage des moteurs
- Valeur `speed > 0` → marche avant, `speed < 0` → marche arrière, `speed = 0` → arrêt

### Contrôle du servo de direction (`steering`)

- Servo connecté sur le **canal 0** du PCA9685
- La direction est issue de `angular.z` du message `Twist`
- Conversion : `angle = 90° + angular.z × 45°` → centré à 90°, borné entre 0° et 180°

### Gestion des modes robot (`mode_callback`)

Le nœud s'abonne au topic `/set_robot_mode` pour changer le comportement du robot :

| Mode | Comportement                                      |
|------|---------------------------------------------------|
| `1`  | Mode par défaut — contrôle normal actif           |
| `3`  | **Arrêt d'urgence** — moteurs coupés immédiatement, commandes `/cmd_vel` ignorées |

Le mode est lu depuis une `String` contenant un entier (ex: `"mode:3"` ou `"3"`).

### Topics ROS 2

| Direction | Topic             | Type                      |
|-----------|-------------------|---------------------------|
| Subscribe | `/cmd_vel`        | `geometry_msgs/Twist`     |
| Subscribe | `/set_robot_mode` | `std_msgs/String`         |

### Matériel utilisé

| Composant         | Interface | Détail                              |
|-------------------|-----------|-------------------------------------|
| PCA9685           | I2C       | Génération PWM (servos + moteurs)   |
| Servo direction   | PCA9685 CH0 | Angle 0°–180°, centré à 90°       |
| Moteur gauche     | PCA9685 CH5 + GPIO 18/17 | PWM + sens        |
| Moteur droit      | PCA9685 CH4 + GPIO 22/27 | PWM + sens        |

---

## Procédure de lancement

### 1. Accéder au workspace ROS 2 sur la Raspberry Pi

```bash
cd ~/ros_ws
```

### 2. Compiler le workspace

```bash
colcon build
```

### 3. Sourcer l'environnement

```bash
source install/setup.bash
```

### 4. Lancer le nœud

```bash
ros2 run robot_controller robot_controller_node
```

---

## Prérequis

- Raspberry Pi 5 avec accès aux GPIO (bibliothèque `lgpio`)
- PCA9685 connecté en I2C (`board.SCL` / `board.SDA`)
- Bibliothèques Python installées :
  - `adafruit-circuitpython-pca9685`
  - `adafruit-circuitpython-motor`
  - `lgpio`
