FROM ros:jazzy-ros-base
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-venv \
    python3-colcon-common-extensions \
    iproute2 \
    iputils-ping \
    nano \
    libgpiod2 \
    python3-lgpio \
    ros-jazzy-rmw-cyclonedds-cpp \
    python3-serial \
    && rm -rf /var/lib/apt/lists/*

# Installer adafruit-blinka dans le Python SYSTÈME pour ROS2
RUN pip3 install --break-system-packages --ignore-installed \
        adafruit-blinka \
        adafruit-circuitpython-pca9685 \
        adafruit-circuitpython-motor \
        RPi.GPIO \
        pyserial

# Venv pour opencv et autres
RUN python3 -m venv /opt/venv
RUN /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install \
        opencv-python \
        adafruit-blinka \
        adafruit-circuitpython-pca9685 \
        adafruit-circuitpython-motor \
        RPi.GPIO \
        pyserial

ENV PATH="/opt/venv/bin:$PATH"
ENV ROS_DOMAIN_ID=52
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ENV ROS_WS=/root/ros_ws

COPY ros_ws/src/ /root/ros_ws/src/
WORKDIR /root/ros_ws

SHELL ["/bin/bash", "-c"]
RUN source /opt/ros/jazzy/setup.bash && \
    colcon build --symlink-install

RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc
RUN echo "source /root/ros_ws/install/setup.bash" >> /root/.bashrc

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
