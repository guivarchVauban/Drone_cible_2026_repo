# Drone_cible_2026_repo
## Répartition des étudiants
- Etudiant 1 : mode manuel &rarr;  <!-- -> --> Timéo BERNARD GOARANT
- Etudiant 2 : mode Autonome &rarr;  <!-- → --> Gatien JAUMOUILLE
- Etudiant 3 : mode verrouillage &rarr;  <!-- → --> Nolan RIBETTE
## Explication des différents modes
- ### Mode manuel
  Le but de ce mode est de pourvoir politer le drone manuellement grâce à une télécommande LoRa. Sur cette télécommande, il sera possible de visionner en temps réel les données essentiels du drone comme la batterie et le gps par exemple. Une application sera développer en parallèle afin de pouvoir choisir le pilote (automatique ou manuel). 
- ### Mode Autonome
  Le but du mode autonome est que le drone puisse ce déplacer en autonomi sans assistance humaine. Pour cela on utilisera la méthode par Waypoints, c'est à dire qu'il faudra pré-définir des différentes coordonnées GPS qui serviront de "chek-points". Il faudra donc aussi crée une interface pour les données GPS ainsi que mettre en place une journalisation des parcours fait par le drone.
  
- ### Mode verouillage
  Le but de ce mode est de détecter visuellement un bateau via la caméra embarqué avec un retour vidéo en temps réel et avec une détection de la cible suite à ses formes, couleurs, gabarit.

## Organisation du Github
Vous avez à votre disposition plusieurs dossiers : 
- [sysml](/sysml) : contient les différents sysml du projet.
- [simulation](/simulation) : contient les script de tests et de simulation du projet.
- [Docs technique](/docs_technique) : l'entièreté des documentation technique des membres du groupe.
- [code](/code) : vous y retrouverez le code source du projet.
 
## Organisation de google Drive
Voici une explication de l'arborescence de notre google drive :
- Compte rendu : contient les comptes rendu des différents sprints.
- Schémas : les différents schémas en lien avec notre projet.
- Soutenance : contient des documents utiles pour la rédaction de la soutenance ainsi que 3 dossiers :
  - Timéo
  - Gatien
  - Nolan
  
  Ils contiennent les rédactions de soutenance de chaques membres du groupe.

Les trois membres du groupe sont Editeur sur l'ensemble du dossier de projet. 

## Synthèse – Technologies utilisées

### • LoRa
Technologie radio longue portée et basse consommation. Utilisée pour l’envoi de données simples sur de longues distances avec un faible débit.  Dans notre cas, la technologie **LoRa** est utilisée pour **lier la télécommande avec le drone cible**.

### • Retour vidéo Wi-Fi unidirectionnel
Transmission du flux vidéo uniquement de l’émetteur vers le récepteur. Offre un débit élevé, mais une portée plus limitée et une consommation plus importante que LoRa. Dans notre cas, elle est utilisée pour **la caméra du drone cible**.

### • GPS
Système de positionnement par satellite permettant de connaître la position, la vitesse et l’heure.  
Indépendant des communications radio.

