#!/bin/bash
source /opt/ros/jazzy/setup.bash

echo "Démarrage ros2_safemode..."

# Lancer robot_mode_manager en arrière-plan
python3 /root/ros_ws/src/mode/mode_manager.py &
PID_MODE=$!
echo "robot_mode_manager démarré (PID $PID_MODE)"

# Lancer buzzer_node en arrière-plan
python3 /root/ros_ws/src/buzzer/buzzer_node.py &
PID_BUZZER=$!
echo "buzzer_node démarré (PID $PID_BUZZER)"

# Si l'un des process meurt, on relance tout
wait -n
echo "Un nœud s'est arrêté — extinction du container"
kill $PID_MODE $PID_BUZZER 2>/dev/null
exit 1
