from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'hand_controller'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Install launch files
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        # Install config files
        *[
            (os.path.join('share', package_name, os.path.dirname(f)), [f])
            for f in glob('config/**/*', recursive=True)
            if os.path.isfile(f)
        ],
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Hoang Dung Dinh',
    maintainer_email='dinhhoangdung0712@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'basic_grasping_policy = hand_controller.basic_grasping_policy:main',
            'number_gesture = hand_controller.number_gesture:main',
            'robot_data_collector = hand_controller.robot_data_collector:main',
            'policy_controller = hand_controller.policy_controller:main',
            'skills_operator = hand_controller.skills.skills_operator:main',
        ],
    },
)
