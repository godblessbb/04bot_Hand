from launch import LaunchDescription
from launch_ros.actions import Node

import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    config_folder = os.path.join(
        get_package_share_directory('hand_controller'),
        'config',
        'weights',
        'robot_policy_model.pth'
    )

    policy_controller_node = Node(
        package='hand_controller',
        executable='policy_controller',
        name='policy_controller_node',
        output='screen',
        parameters=[
            {'model_path': config_folder},
        ]
    )
    return LaunchDescription([
        policy_controller_node,
    ])