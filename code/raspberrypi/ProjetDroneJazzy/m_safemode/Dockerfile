FROM ros:jazzy

RUN apt update && apt install -y \
    nano \
    python3-pip \
    python3-gpiozero \
    python3-lgpio \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-std-msgs \
    && rm -rf /var/lib/apt/lists/*

RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc

WORKDIR /root/ros_ws

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"]
