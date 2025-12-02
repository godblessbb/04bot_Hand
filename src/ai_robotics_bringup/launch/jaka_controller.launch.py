from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # AUBO controller and moveit launch
    jaka_driver_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('jaka_planner'), 'launch', 'moveit_server.launch.py')
        ),
        launch_arguments={
            'ip': '192.168.10.228',
            'model': 'minicobo',
        }.items(),
    )

    jaka_controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('jaka_minicobo_moveit_config'), 'launch', 'demo.launch.py')
        ),
    )

    jaka_executor_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('jaka_minicobo_moveit_config'), 'launch', 'executor.launch.py')
        ),
    )

    orca_hand_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('orca_hand_hardware_interface'), 'launch', 'orca_hand.launch.py')
        ),
        launch_arguments={
        }.items(),
    )

    return LaunchDescription([
        jaka_driver_launch,
        jaka_controller_launch,
        jaka_executor_launch,
        # aubo_moveit_launch,
    ])