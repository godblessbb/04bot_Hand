from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    """
    Hardware launch
    """
    camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('orbbec_camera'), 'launch', 'astra_pro2.launch.py')
        ),
        launch_arguments={
            'camera_name': 'astra',
            'camera_frame_id': 'camera_link',
            'color_format': 'MJPG',
            'color_fps': '30',
            'depth_format': 'Y11',
            'depth_fps': '30',
            'depth_registration': 'true',
            'enable_ir': 'false',
        }.items(),
    )

    """
    Software launch
    """
    voice_command_node = Node(
        package='natural_language_commander',
        executable='voice_to_command',
        name='voice_to_command',
        output='screen',
    )

    open_yolo_detector_node = Node(
        package='natural_language_commander',
        executable='open_yolo_detector',
        name='open_yolo_detector',
        output='screen',
    )

    camera_transform_broadcaster = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_tf_broadcaster',
        arguments=['-0.923', '-0.093', '0.58', '0.091', '0.47', '.04', 'world', 'astra_link'], # xyz, ypr
    )


    return LaunchDescription([
        camera_launch,
        voice_command_node,
        open_yolo_detector_node,
        camera_transform_broadcaster,
    ])