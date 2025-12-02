from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'orca_hand_hardware_interface'

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
    zip_safe=True,
    maintainer='Hoang Dung Dinh',
    maintainer_email='dinhhoangdung0712@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'hand_controller_node = orca_hand_hardware_interface.hand_controller_node:main',
        ],
    },
)
