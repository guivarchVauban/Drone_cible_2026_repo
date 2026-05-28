# bridge_manette_node

## Description

Ce nœud ROS 2 fait office de **pont entre la manette de contrôle et le réseau LoRa**. Il tourne sur la **VM de contrôle** (`util@ubuntu`) et assure deux rôles principaux : envoyer les commandes joystick vers le drone via LoRa, et recevoir les données télémétriques du drone (GPS, IMU, détections) pour les republier en topics ROS 2.

---

## Ce que fait le nœud

### Réception joystick → émission LoRa (`joy_callback`)

- S'abonne au topic `/joy` (type `sensor_msgs/Joy`)
- Récupère les deux premiers axes du joystick (`axes[0]` et `axes[1]`)
- Mappe les valeurs :
  - `axes[0]` → `[0, 255]` (direction)
  - `axes[1]` → `[0, 20]` (vitesse)
- Construit une trame de 5 octets : `[0x52, 0x08, 0x02, x0_mapped, x1_mapped]`
- Envoie la trame via UART avec la commande `AT+SEND=0,...`
- **Anti-spam** : suspend l'envoi si les valeurs sont stables depuis plus d'1 seconde

### Réception LoRa → publication ROS 2 (`read_serial`)

Lit les lignes UART contenant `HEX:` et dispatche selon le type de trame :

| Type de trame | Contenu                        | Topic publié      | Type de message     |
|---------------|--------------------------------|-------------------|---------------------|
| `0x01`        | GPS (latitude + longitude)     | `/gps`            | `NavSatFix`         |
| `0x02`        | IMU (quaternion + gyroscope)   | `/boussole`       | `Imu` (orientation) |
|               |                                | `/inclinometre`   | `Imu` (angular vel) |
| `0x03`        | Détections rectangles (YOLO)   | `/rectangle`      | `String` (JSON)     |

### Topics ROS 2

| Direction | Topic               | Type              |
|-----------|---------------------|-------------------|
| Subscribe | `/joy`              | `sensor_msgs/Joy` |
| Publish   | `/gps`              | `sensor_msgs/NavSatFix` |
| Publish   | `/boussole`         | `sensor_msgs/Imu` |
| Publish   | `/inclinometre`     | `sensor_msgs/Imu` |
| Publish   | `/rectangle`        | `std_msgs/String` |

---

## Procédure de lancement

### 1. Accéder au répertoire de travail

```bash
cd /home/util/Documents/Projet/ros2_remote/ros_ws
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
ros2 run bridge_manette bridge_manette_node
```

---

## Prérequis

- Port série disponible sur `/dev/ttyUSB0` (module LoRa connecté en UART)
- Package `pyserial` installé
- Joystick connecté et vérifier qu'il est bien brancher en `/dev/input/js0`. Si vous êtes sur une VM, il sera très certainement en `js2`. Si c'est le cas alors lancer la commande : 
```bash
sudo ln -sf /dev/input/js2 /dev/input/js0
```
- nœud `joy` actif (ex: `ros2 run joy joy_node`)
