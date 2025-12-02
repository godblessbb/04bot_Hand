from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # AUBO controller and moveit launch
    aubo_controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('aubo_ros2_driver'), 'launch', 'aubo_control.launch.py')
        ),
        launch_arguments={
            'aubo_type': 'aubo_i3',
            'robot_ip': '192.168.10.101',
        }.items(),
    )

    aubo_moveit_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('aubo_moveit_config'), 'launch', 'aubo_moveit.launch.py')
        ),
        launch_arguments={
            'aubo_type': 'aubo_i3',
        }.items(),
    )

    orca_hand_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('orca_hand_hardware_interface'), 'launch', 'orca_hand.launch.py')
        ),
        launch_arguments={
        }.items(),
    )

    return LaunchDescription([
        aubo_controller_launch,
        aubo_moveit_launch,
        # orca_hand_launch,
    ])