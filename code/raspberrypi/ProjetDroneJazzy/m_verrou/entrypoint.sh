#!/bin/bash
set -e

# Source ROS2
source /opt/ros/jazzy/setup.bash

# Source workspace si build
if [ -f "/root/ros_ws/install/setup.bash" ]; then
    source /root/ros_ws/install/setup.bash
fi

echo "🚀 Starting ROS2 nodes..."

# Lancer la caméra en background
ros2 run usb_cam usb_cam_node_exe &
sleep 2

# Lancer ton détecteur YOLO
ros2 run boat_detector yolo_node &

ros2 run navigation_node navigation &
# Garder le container actif
wait
