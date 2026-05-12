#!/bin/bash
source /opt/ros/jazzy/setup.bash
source /root/ros_ws/install/setup.bash

ros2 run bridge_drone bridge_drone_node &
ros2 run robot_controller controller &

tail -f /dev/null
