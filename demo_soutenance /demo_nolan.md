# Checklist Démo Projet — Ma Partie

---

## 1. usb_cam & boat_detection

- [ ] **1.1** Lancer le nœud `usb_cam` (lancement automatique)
- [ ] **1.2** Vérifier son bon fonctionnement :
```bash
  ros2 topic list & ros2 node list
```
- [ ] **1.3** Lancer `boat_detection` (lancement automatique) vérifier les détections publiées :
```bash
  ros2 topic echo /boat_detection_json
```
- [ ] **1.4** Montrer le dashboard Node-RED dans le même onglet : flux vidéo en direct et bateau détecté
- [ ] **1.5** Passer un bateau devant la caméra et vérifier si les rectangles s'affiche 
  > Vérifier labels, confiance et position des détections

---

## 2. navigation_verrou

- [ ] **2.1** Lancer le nœud `navigation_verrou` (lancement automatique)
- [ ] **2.2** Vérifier l'état du verrou de navigation :
```bash
  ros2 node list
```
- [ ] **2.3** Déclencher l'activation / désactivation du verrou et observer le changement d'état en temps réel sur le topic
- [ ] **2.4** Vérifier que les `/cmd_vel` sont bien publié
  > Aucune commande de vitesse ne doit passer pendant le verrouillage

---

## 3. watchdog_system 

- [ ] **3.1** Lancer `watchdog_system` et vérifier les topics publiés :
```bash
  ros2 topic echo /etat_node
```
**Pour information :**<br>
<br>Aucun problème = 54<br>
problème nœud dans docker manuel = 55<br>
problème nœud dans docker auto = 66<br>
problème nœud dans docker verrou = 77

## 4. watchdog radio

- [ ] **3.2** Lancer publisherWatchdog puis simulation d'un problème avec un freeze
- [ ] **3.3** Lancer `watchdog_radio` et vérifier la publication du mode 3 :
```bash
  ros2 topic echo /robot_mode
```
- [ ] **3.4** Vérifiez que cmd_vel publie 0 en mode 3 et que les moteurs ne fonctionnent plus

---

## 5. Buzzer *(Bonus)*

- [ ] **4.1** Vérifier que le nœud buzzer est actif :
```bash
  ros2 node list
```
- [ ] **4.2** Montrer le buzzer se déclencher automatiquement lors d'une alerte watchdog_radio (passage en mode 3) et vérifiez si il fait sonner l'alerte
```bash
  ros2 topic echo /robot_mode
```
