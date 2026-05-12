FROM ros:humble-ros-base

ENV DEBIAN_FRONTEND=noninteractive

# Dépendances système et ROS
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    flask \
    nano \
    iproute2 \
    iputils-ping \
    gpsd \
    gpsd-clients \
    python3-gps \
    ros-humble-rmw-cyclonedds-cpp \
    pip3 install smbus2 \
    pip3 install pynmea2 \
    && rm -rf /var/lib/apt/lists/*

# Workspace ROS
ENV ROS_WS=/root/ros_ws
RUN mkdir -p $ROS_WS/src
WORKDIR $ROS_WS

# Source ROS automatiquement
SHELL ["/bin/bash", "-c"]
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc && \
    echo "source /root/ros_ws/install/setup.bash" >> /root/.bashrc

CMD ["bash"]
