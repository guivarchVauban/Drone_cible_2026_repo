FROM ros:jazzy-ros-base

ENV DEBIAN_FRONTEND=noninteractive

# Dépendances système et ROS
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    python3-colcon-common-extensions \
    nano \
    iproute2 \
    iputils-ping \
    gpsd \
    gpsd-clients \
    python3-gps \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-nmea-navsat-driver \
    ros-jazzy-robot-localization \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install flask smbus2

ENV PATH="/opt/venv/bin:$PATH"
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# Workspace ROS
ENV ROS_WS=/root/ros_ws
RUN mkdir -p $ROS_WS/src
WORKDIR $ROS_WS

# Source ROS automatiquement
SHELL ["/bin/bash", "-c"]
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc && \
    echo "source /root/ros_ws/install/setup.bash" >> /root/.bashrc

CMD ["bash"]
