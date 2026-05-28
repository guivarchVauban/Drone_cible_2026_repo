# 🎯 navigation_verrouillage — Nœud ROS 2 de verrouillage automatique de cible

Nœud ROS 2 assurant le **verrouillage automatique d’un bateau détecté par YOLOv8**.
Lorsque le mode verrouillage est actif (`robot_mode = 2`), le robot analyse les coordonnées de la cible détectée et génère automatiquement des commandes de navigation afin de garder le bateau centré dans le champ de vision.

---

## Fonctionnement

```text
/image_raw ──► boat_detector ──► /boat_detection_json
                                          │
                                          ▼
                               navigation_verrouillage
                                          │
                                          ▼
                                      /cmd_vel

/robot_mode ──────────────────────────────▲
```

---

## Pipeline

1. **Réception des détections** via le topic `/boat_detection_json`
2. **Lecture du mode robot** via `/robot_mode`
3. **Validation du mode verrouillage**

   * si `robot_mode != 2` → arrêt immédiat du suivi
4. **Calcul du centre de la cible**

   * récupération de la bounding box du bateau
   * calcul du centre horizontal du bateau
5. **Calcul de l’erreur**

   * différence entre le centre du bateau et le centre de l’image
6. **Application du correcteur proportionnel**

   * correction angulaire appliquée sur `/cmd_vel`
7. **Publication des commandes moteur**

   * avance constante
   * correction de direction automatique

---

## Loi de commande

| Paramètre        | Valeur         | Description                 |
| ---------------- | -------------- | --------------------------- |
| `linear.x`       | `0.6 m/s`      | Vitesse d’avance constante  |
| `angular.z`      | `-Kp × erreur` | Correction de direction     |
| `Kp`             | `0.002`        | Gain proportionnel          |
| `dead_zone`      | `20 px`        | Zone morte anti-oscillation |
| `image_center_x` | `320 px`       | Centre horizontal image     |

---

## Topics

| Topic                  | Type                  | Rôle                                |
| ---------------------- | --------------------- | ----------------------------------- |
| `/boat_detection_json` | `std_msgs/String`     | Entrée — coordonnées YOLO du bateau |
| `/robot_mode`          | `std_msgs/String`     | Entrée — mode du robot              |
| `/cmd_vel`             | `geometry_msgs/Twist` | Sortie — commandes de navigation    |

---

## Format JSON attendu

```json
{
  "timestamp": 1740000000.12,
  "num_boats": 1,
  "boats": [
    {
      "x_center": 412.5,
      "y_center": 201.2,
      "width": 85.0,
      "height": 62.0,
      "confidence": 0.91
    }
  ]
}
```

---

## Calcul effectué

### Centre du bateau

```python
boat_center_x = x_center
```

### Erreur horizontale

```python
error = image_center_x - boat_center_x
```

### Correction proportionnelle

```python
angular_z = -Kp * error
```

---

## Comportement du système

| Situation            | Action                      |
| -------------------- | --------------------------- |
| `robot_mode != 2`    | Arrêt complet du suivi      |
| Aucun bateau détecté | Robot immobile              |
| Bateau centré        | Pas de correction angulaire |
| Bateau à gauche      | Rotation vers la gauche     |
| Bateau à droite      | Rotation vers la droite     |

---

## Fréquence de fonctionnement

| Élément                | Fréquence              |
| ---------------------- | ---------------------- |
| Réception caméra       | dépend de `/image_raw` |
| Détection YOLOv8       | ~5 FPS                 |
| Boucle de contrôle     | 20 Hz                  |
| Publication `/cmd_vel` | temps réel             |

---

## Prérequis

* ROS 2 Jazzy / Humble
* Python 3.10+
* `geometry_msgs`
* `std_msgs`
* `boat_detector` fonctionnel
* YOLOv8 opérationnel
* Caméra USB publiée sur `/image_raw`

---

## Lancement

### 1. Construction du workspace

```bash
cd ~/ros_ws

colcon build --symlink-install

source install/setup.bash
```

---

### 2. Lancer le nœud

```bash
ros2 run navigation_node navigation_verrouillage
```

---

### 3. Vérifier les topics

```bash
ros2 topic list
```

---

## Tests manuels

### Activer le mode verrouillage

```bash
ros2 topic pub /robot_mode std_msgs/String "data: '2'"
```

---

### Simuler une détection

```bash
ros2 topic pub /boat_detection_json std_msgs/String \
"data: '{\"boats\": [{\"x_center\": 450.0, \"width\": 100.0, \"height\": 80.0, \"confidence\": 0.92}]}'"
```

---

### Observer les commandes moteur

```bash
ros2 topic echo /cmd_vel
```

Résultat attendu :

```yaml
linear:
  x: 0.6

angular:
  z: négatif
```

Le robot doit corriger sa trajectoire vers la droite.

---

## Structure du code

```text
navigation_verrouillage.py
├── class NavigationNode(Node)
│   ├── __init__()
│   ├── mode_callback()
│   ├── detection_callback()
│   ├── control_loop()
│   └── stop_robot()
└── main()
```

---

## Sécurité

| Cas                  | Protection                       |
| -------------------- | -------------------------------- |
| Perte de détection   | arrêt du robot                   |
| Changement de mode   | arrêt immédiat                   |
| JSON invalide        | ignoré                           |
| Arrêt brutal du node | `/cmd_vel` cesse automatiquement |

---

## Auteur

**Nolan RIBETTE**
BTS CIEL IR — Projet Drone Cible Marine Nationale — 2026
