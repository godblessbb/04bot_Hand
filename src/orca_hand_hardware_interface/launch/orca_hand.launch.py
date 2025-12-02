from launch import LaunchDescription
from launch_ros.actions import Node

import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    config_folder = os.path.join(
        get_package_share_directory('orca_hand_hardware_interface'),
        'config',
        'models',
        'orcahand_v1_right'
    )

    hand_controller_node = Node(
        package='orca_hand_hardware_interface',
        executable='hand_controller_node',
        name='hand_controller_node',
        output='screen',
        parameters=[
            {'config_folder': config_folder},
            {'use_sim_time': False},
        ]
    )
    return LaunchDescription([
        hand_controller_node,
    ])