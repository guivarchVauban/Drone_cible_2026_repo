# Interface Node-RED — Procédure de lancement

## Description

L'interface de contrôle de la mission repose sur **Node-RED**, un outil de programmation visuelle accessible depuis un navigateur. Elle communique avec ROS 2 via un bridge WebSocket, récupère le flux vidéo du drone en WiFi, et peut afficher des points GPS préparés avant la mission.

---

## Architecture

```
Raspberry Pi (drone)          VM de contrôle (util@ubuntu)
─────────────────────         ──────────────────────────────
ROS 2 topics                  rosbridge_server (WebSocket)
flux caméra                   web_video_server
fichiers JSON (Waypoints)  →  montage Samba → Node-RED
```

---

## Procédure de lancement

### 1. Lancer le bridge ROS 2 ↔ WebSocket

Ce bridge permet à Node-RED de communiquer avec les topics ROS 2 via WebSocket.

```bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

> Le bridge écoute par défaut sur le port **9090**.

---

### 2. Lancer Node-RED

```bash
node-red
```

> L'interface est ensuite accessible depuis un navigateur à l'adresse :
> **http://localhost:1880**

---

### 3. Lancer le serveur vidéo (flux WiFi)

Pour recevoir le flux vidéo de la caméra du drone via WiFi :

```bash
ros2 run web_video_server web_video_server
```

> Le flux est accessible dans Node-RED ou navigateur à l'adresse :
> **http://\<IP_drone\>:8080/stream?topic=/\<topic_camera\>**

---

## Affichage des waypoints GPS (Alternative simple)
Se connecter à l'IP du drone avec un logiciel d'échange de fichier comme winscp ou filezilla, prendre le fichier sur la Raspberry et le mettre sur la VM au bon emplacement.

## Affichage des waypoints GPS (Alternative avancée)

Si des points GPS ont été préparés avant la mission et stockés en JSON sur la Raspberry Pi, suivre les étapes ci-dessous pour les monter et les rendre accessibles à Node-RED.

### 1. Vérifier que Samba est actif sur la Raspberry Pi

Se connecter à la Raspberry Pi et vérifier le service :

```bash
sudo systemctl status smbd
```

> Le service doit être `active (running)`. S'il est arrêté, le démarrer avec :
> ```bash
> sudo systemctl start smbd
> ```

### 2. Monter le dossier partagé sur la VM

Depuis la VM de contrôle (`util@ubuntu`) :

```bash
sudo mount -t cifs //172.25.28.12/Waypoints ~/raspi_waypoints \
  -o credentials=/home/util/.smbcredentials,uid=$(id -u),gid=$(id -g)
```

> - `//172.25.28.12/Waypoints` : partage réseau sur la Raspberry Pi
> - `~/raspi_waypoints` : point de montage local (créer le dossier si nécessaire : `mkdir ~/raspi_waypoints`)
> - `/home/util/.smbcredentials` : fichier contenant les identifiants Samba

### 3. Vérifier que le fichier JSON est bien accessible

```bash
ls ~/raspi_waypoints
```

Le fichier JSON des waypoints peut ensuite être lu directement par Node-RED depuis `~/raspi_waypoints/`.

### Démonter le partage (fin de mission)

```bash
sudo umount ~/raspi_waypoints
```

---

## Récapitulatif des commandes

| Étape                        | Commande                                                                 |
|------------------------------|--------------------------------------------------------------------------|
| Bridge ROS 2 WebSocket       | `ros2 launch rosbridge_server rosbridge_websocket_launch.xml`            |
| Interface Node-RED           | `node-red`                                                               |
| Flux vidéo WiFi              | `ros2 run web_video_server web_video_server`                             |
| Vérifier Samba (Raspi)       | `sudo systemctl status smbd`                                             |
| Monter waypoints JSON        | `sudo mount -t cifs //172.25.28.12/Waypoints ~/raspi_waypoints -o credentials=/home/util/.smbcredentials,uid=$(id -u),gid=$(id -g)` |
| Démonter waypoints           | `sudo umount ~/raspi_waypoints`                                          |
