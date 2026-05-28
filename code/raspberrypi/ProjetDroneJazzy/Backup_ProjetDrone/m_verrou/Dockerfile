FROM ros:humble-ros-base

ENV DEBIAN_FRONTEND=noninteractive

# Installer dépendances ROS et outils
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    iproute2 \
    iputils-ping \
    nano \
    ros-humble-rmw-cyclonedds-cpp \
    ros-humble-usb-cam \
    libgpiod2 \
    v4l-utils \
    ffmpeg \
    python3-opencv \
    ros-humble-cv-bridge \
    ros-humble-image-transport \
    ros-humble-vision-msgs \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Installer bibliothèques Python supplémentaires
RUN pip3 install adafruit-circuitpython-pca9685 adafruit-circuitpython-motor RPi.GPIO
RUN pip3 install --no-cache-dir \
RUN pip3 install ultralytics \
    numpy==1.24.4 \
    pandas==1.5.3 \
    torch \
    torchvision \
    opencv-python \
    tqdm \
    seaborn \
    matplotlib

# Variables ROS
ENV ROS_DOMAIN_ID=52
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# Créer workspace ROS
ENV ROS_WS=/root/ros_ws
RUN mkdir -p $ROS_WS/src
WORKDIR $ROS_WS

# Setup ROS
SHELL ["/bin/bash", "-c"]
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc

CMD ["bash"]

