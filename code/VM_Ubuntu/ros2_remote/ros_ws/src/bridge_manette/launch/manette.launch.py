from launch import LaunchDescription
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    joy_params = os.path.join(
        get_package_share_directory('bridge_manette'),
        'config', 'joy_params.yaml'
    )

    return LaunchDescription([
        Node(
            package='joy',
            executable='joy_node',
            name='joy_node',
            parameters=[joy_params]
        ),
        Node(
            package='bridge_manette',
            executable='bridge_manette_node',
            name='bridge_manette',
            output='screen'
        ),
    ])
