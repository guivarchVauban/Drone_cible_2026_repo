# Drone Cible

## Informations générales

**Mot de passe VM Ubuntu :**

```text
Projet_Drone2026
```

---

## Compilation d'un seul nœud

```bash
colcon build --packages-select [nom_du_noeud]
```

## Publication sur `set_robot_mode`

```bash
ros2 topic pub /set_robot_mode std_msgs/msg/String \
"data: '1'"
```

---

# Ordre de lancement des nœuds du mode autonome

## 1. IMU Node

```bash
source install/setup.bash
ros2 run imu_node imu_data
```

---

## 2. NavSat Driver

```bash
source install/setup.bash
ros2 run nmea_navsat_driver nmea_serial_driver \
  --ros-args \
  -p port:=/dev/ttyUSB1 \
  -p baud:=4800
```

---

## 3. Node Consigne

```bash
source install/setup.bash
ros2 run node_consigne node_consigne
```

---

## 4. EKF (Extended Kalman Filter)

```bash
source install/setup.bash
ros2 run robot_localization ekf_node --ros-args --params-file ~/ros_ws/config/ekf.yaml
```

---

## 5. NavSat Transform

```bash
source install/setup.bash

ros2 run robot_localization navsat_transform_node \
  --ros-args --params-file ~/ros_ws/config/navsat.yaml \
  -r gps/fix:=/fix \
  -r imu/data:=/imu/data \
  -r odometry/filtered:=/odometry/filtered \
  -r gps/filtered:=/Nav_sat_fix_transformed
```

---

## 6. Navigation Automatique

```bash
source install/setup.bash
ros2 run node_navigation_auto node_navigation_auto
```

---

# Configuration de la simulation

## Désactiver, activer ou modifier une fonctionnalité

Fichier concerné :

```text
/training_zone/src/vrx/vrx_gz/src/vrx_gz/model.py
```

Dans la fonction :

```python
def xacro_mcd(self)
```

Modifier les valeurs :

```python
True
```

ou

```python
False
```

selon les fonctionnalités souhaitées.

Puis recompiler :

```bash
colcon build
```

et relancer la simulation :

```bash
./launch.sh
```

Pour modifier les frequence des composants: 

```text
/home/gatien/training_zone/src/vrx/vrx_urdf/wamv_gazebo/urdf/components/wamv_imu.xacro
```
