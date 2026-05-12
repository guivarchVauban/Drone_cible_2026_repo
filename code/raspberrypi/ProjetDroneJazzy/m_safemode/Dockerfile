FROM ros:jazzy

# Installer outils + Docker CLI + dépendances ROS
RUN apt update && apt install -y \
    nano \
    python3-pip \
    docker.io \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-std-msgs \
    && rm -rf /var/lib/apt/lists/*

# Workspace ROS2
WORKDIR /root/ros_ws

# Copier ton code dans le container
COPY . /root/ros_ws

# Build ROS2 workspace
RUN . /opt/ros/jazzy/setup.sh && colcon build

# Source ROS automatiquement
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc
RUN echo "source /root/ros_ws/install/setup.bash" >> /root/.bashrc

