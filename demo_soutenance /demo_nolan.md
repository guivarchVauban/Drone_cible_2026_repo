# Checklist Démo Projet — Ma Partie

---

## 1. usb_cam & boat_detection

- [ ] **1.1** Lancer le nœud `usb_cam` et vérifier son démarrage correct dans les logs
- [ ] **1.2** Vérifier la publication du topic image :
```bash
  ros2 topic echo /image_raw
```
- [ ] **1.3** Lancer `boat_detection` et vérifier les détections publiées :
```bash
  ros2 topic echo /boat_detections
```
- [ ] **1.4** Montrer le dashboard Node-RED dans le même onglet : flux vidéo en direct + overlay des bounding boxes des bateaux détectés
- [ ] **1.5** Passer un bateau devant la caméra et vérifier la cohérence des données topic ↔ dashboard en temps réel
  > Vérifier labels, confiance et position des détections

---

## 2. navigation_verrou

- [ ] **2.1** Lancer le nœud `navigation_verrou` et vérifier son démarrage correct dans les logs
- [ ] **2.2** Vérifier l'état du verrou de navigation :
```bash
  ros2 topic echo /navigation_lock
```
- [ ] **2.3** Déclencher l'activation / désactivation du verrou et observer le changement d'état en temps réel sur le topic
- [ ] **2.4** Vérifier que les `/cmd_vel` sont bien bloquées lorsque le verrou est actif
  > Aucune commande de vitesse ne doit passer pendant le verrouillage

---

## 3. watchdog_system & watchdog radio

- [ ] **3.1** Lancer `watchdog_system` et vérifier les heartbeats publiés :
```bash
  ros2 topic echo /watchdog_status
```
- [ ] **3.2** Simuler la perte d'un nœud critique et observer la réaction du watchdog (alerte / arrêt d'urgence)
- [ ] **3.3** Lancer `watchdog_radio` et vérifier la surveillance du lien radio :
```bash
  ros2 topic echo /radio_status
```
- [ ] **3.4** Simuler une perte de liaison radio et vérifier le comportement de sécurité déclenché (arrêt, mode sûr…)
  > Vérifier le délai de timeout et la procédure de failsafe

---

## 4. Buzzer *(Bonus)*

- [ ] **4.1** Vérifier que le topic buzzer est actif :
```bash
  ros2 topic echo /buzzer
```
- [ ] **4.2** Publier manuellement une commande de bip et vérifier le déclenchement physique :
```bash
  ros2 topic pub /buzzer std_msgs/Bool "data: true"
```
- [ ] **4.3** Montrer le buzzer se déclencher automatiquement lors d'une alerte watchdog (intégration bout-en-bout)
