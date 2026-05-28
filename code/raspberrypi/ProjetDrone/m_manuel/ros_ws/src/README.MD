# bridge_drone_node

## Description

Ce nœud ROS 2 fait office de **pont entre le drone et le réseau LoRa**. Il tourne sur la **Raspberry Pi du drone** (`util@DroneCible`) dans le conteneur Docker `ros2_manuel`, et assure deux rôles principaux : transmettre les données capteurs du drone (IMU, GPS, détections) vers la manette via LoRa, et recevoir les commandes joystick pour les republier en commandes de mouvement.

---

## Ce que fait le nœud

### Émission capteurs → LoRa

| Callback            | Topic source            | Trame émise | Contenu                                    |
|---------------------|-------------------------|-------------|--------------------------------------------|
| `imu_callback`      | `/imu/data`             | `0x02`      | Quaternion (ox, oy, oz, ow) + gyroscope (avx, avy, avz), encodés en `float` little-endian |
| `gps_callback`      | `/fix`                  | `0x01`      | Latitude + longitude encodées en `float` little-endian |
| `detection_callback`| `/boat_detection_json`  | `0x03`      | Liste de bounding boxes `{x, y, width, height}` en entiers 16 bits little-endian |

Chaque trame commence par `[0x52, type, longueur]` puis le payload.

### Réception LoRa → commande de mouvement (`read_serial`)

- Lit les lignes UART contenant `HEX:`
- Reconnaît les trames de type `0x08` (commande joystick depuis la manette)
- Décode les deux valeurs mappées et les convertit en vitesses normalisées :
  - `x0_mapped` → vitesse angulaire (`angular.z`)
  - `x1_mapped` → vitesse linéaire (`linear.x`)
- Applique un seuil mort de ±0.02 pour éviter les dérives
- Publie sur `/cmd_vel` (type `Twist`)

### Topics ROS 2

| Direction | Topic                   | Type                    |
|-----------|-------------------------|-------------------------|
| Subscribe | `/imu/data`             | `sensor_msgs/Imu`       |
| Subscribe | `/fix`                  | `sensor_msgs/NavSatFix` |
| Subscribe | `/boat_detection_json`  | `std_msgs/String`       |
| Publish   | `/cmd_vel`              | `geometry_msgs/Twist`   |

### Paramètres configurables

| Paramètre           | Valeur par défaut | Description                        |
|---------------------|-------------------|------------------------------------|
| `port`              | `/dev/ttyUSB0`    | Port série du module LoRa          |
| `baudrate`          | `9600`            | Vitesse de communication UART      |
| `max_linear_speed`  | `1.0`             | Vitesse linéaire maximale (m/s)    |
| `max_angular_speed` | `1.0`             | Vitesse angulaire maximale (rad/s) |

---

## Procédure de lancement

### 1. Se connecter au conteneur Docker sur la Raspberry Pi

```bash
sudo docker exec -it ros2_manuel bash
```

### 2. Accéder au workspace ROS 2

```bash
cd ~/ros_ws
```

### 3. Compiler le workspace

```bash
colcon build
```

### 4. Sourcer l'environnement

```bash
source install/setup.bash
```

### 5. Lancer le nœud

```bash
ros2 run bridge_drone bridge_drone_node
```

### Lancement avec paramètres personnalisés (optionnel)

```bash
ros2 run bridge_drone bridge_drone_node --ros-args \
  -p port:=/dev/ttyUSB0 \
  -p baudrate:=9600 \
  -p max_linear_speed:=1.5 \
  -p max_angular_speed:=1.0
```

---

## Prérequis

- Port série disponible sur `/dev/ttyUSB0` (module LoRa connecté en UART)
- Package `pyserial` installé
- Nœuds IMU (`/imu/data`) et GPS (`/fix`) actifs sur le drone
- Nœud de détection actif si utilisation du topic `/boat_detection_json`
