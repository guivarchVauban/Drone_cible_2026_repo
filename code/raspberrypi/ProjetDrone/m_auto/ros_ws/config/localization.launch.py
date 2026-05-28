from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    ekf_config    = '/root/ros_ws/config/ekf.yaml'
    navsat_config = '/root/ros_ws/config/navsat.yaml'

    return LaunchDescription([

        # Noeud 1 : EKF — fusionne IMU + odometrie GPS
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[ekf_config],
            remappings=[
                ('odometry/filtered', '/odometry/filtered'),
            ]
        ),

        # Noeud 2 : navsat_transform — convertit /fix en odometrie cartesienne
        Node(
            package='robot_localization',
            executable='navsat_transform_node',
            name='navsat_transform_node',
            output='screen',
            parameters=[navsat_config],
            remappings=[
                ('gps/fix',           '/fix'),
                ('imu/data',          '/imu/data'),
                ('odometry/filtered', '/odometry/filtered'),
                ('gps/filtered',      '/Nav_sat_fix_transformed'),
            ]
        ),
    ])
