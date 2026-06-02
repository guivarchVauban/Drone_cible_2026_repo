# Checklist Démo Projet

---

## 1. Dashboard Node-RED

- [ ] **1.1** Montrer les différentes fenêtres du dashboard
- [ ] **1.2** Montrer le changement de mode en exécutant :
  ```bash
  ros2 topic echo /robot_mode
  ```
- [ ] **1.3** Montrer la position GPS du drone sur la carte avec les waypoints
- [ ] **1.4** Montrer le GPS et l'IMU en mouvement

---

## 2. Lancer les bridges

- [ ] **2.0** Lancer `bridge_manette_node.py` et `bridge_robot_node.py`
- [ ] **2.1** Vérifier les données joystick / commandes vitesse sur la VM :
  ```bash
  ros2 topic echo /joy
  ros2 topic echo /cmd_vel
  ```
  > Comparer les données et vérifier leur justesse

- [ ] **2.2** Vérifier les données IMU :
  ```bash
  ros2 topic echo /inclinometre
  ros2 topic echo /boussole
  ```

- [ ] **2.3** Vérifier les données GPS :
  ```bash
  ros2 topic echo /gps
  ```

---

## 3. Démo envoi de trame — PicoScope

### Réglages matériels
- [ ] **3.1** Brancher le PicoScope sur les broches **RX** et **GND** du LA66

### Configuration logicielle
- [ ] **3.2** Ouvrir le décodeur **Série**
- [ ] **3.3** Sélectionner le protocole **RS232 UART**
- [ ] **3.4** Afficher en mode **Graphique Hexa / Tableau ASCII–Hex**
- [ ] **3.5** Envoyer la trame et vérifier la réception sur le PicoScope

---
