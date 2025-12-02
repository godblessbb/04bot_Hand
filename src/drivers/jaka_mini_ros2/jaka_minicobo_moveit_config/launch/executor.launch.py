from moveit_configs_utils import MoveItConfigsBuilder
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    moveit_config = MoveItConfigsBuilder("jaka_minicobo", package_name="jaka_minicobo_moveit_config").to_moveit_configs()
    return LaunchDescription([
        Node(
            package="jaka_minicobo_moveit_config",
            executable="moveit_executor_node",
            name="moveit_executor_main_node",
            output="screen",
            parameters=[
                moveit_config.to_dict(),
            ],
        )
    ])
