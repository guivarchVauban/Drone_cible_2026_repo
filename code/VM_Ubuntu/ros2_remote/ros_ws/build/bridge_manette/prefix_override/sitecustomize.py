import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/util/Documents/Projet/ros2_remote/ros_ws/install/bridge_manette'
