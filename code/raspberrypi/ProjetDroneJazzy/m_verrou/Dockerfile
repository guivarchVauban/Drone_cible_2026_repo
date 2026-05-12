FROM ros:jazzy-ros-base

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DEFAULT_TIMEOUT=1000

# =========================
# DEPENDANCES SYSTEME
# =========================
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-opencv \
    python3-catkin-pkg \
    ros-jazzy-cv-bridge \
    ros-jazzy-image-transport \
    ros-jazzy-vision-msgs \
    ros-jazzy-usb-cam \
    ros-jazzy-rmw-cyclonedds-cpp \
    v4l-utils \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    iproute2 \
    iputils-ping \
    nano \
    git \
    && rm -rf /var/lib/apt/lists/*

# =========================
# PYTHON (SANS VENV)
# =========================

# 1. Installer TORCH CPU (évite gros bug pip + timeout)
RUN pip3 install --break-system-packages --retries 10 \
    torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cpu

# 2. Installer YOLO + dépendances
RUN pip3 install --break-system-packages --retries 10 \
    ultralytics \
    numpy==1.26.4 \
    opencv-python \
    pandas \
    tqdm \
    seaborn \
    matplotlib

# =========================
# VARIABLES ROS
# =========================
ENV ROS_DOMAIN_ID=52
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# =========================
# WORKSPACE ROS
# =========================
ENV ROS_WS=/root/ros_ws
RUN mkdir -p $ROS_WS/src
WORKDIR $ROS_WS

# =========================
# AUTO SOURCE
# =========================
SHELL ["/bin/bash", "-c"]
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc

# =========================
# ENTRYPOINT
# =========================
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
