FROM ros:humble

# Installer outils + dépendances nécessaires
RUN apt update && apt install -y \
    nano \
    python3-pip \
    ros-humble-rmw-cyclonedds-cpp \
    ros-humble-std-msgs \
    && rm -rf /var/lib/apt/lists/*

# Charger ROS automatiquement
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc

WORKDIR /root/ros_ws

CMD ["bash", "-c", "source /opt/ros/humble/setup.bash && python3 /root/ros_ws/src/mode/robot_mode_manager.py"]
