from setuptools import find_packages, setup

package_name = 'natural_language_commander'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
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
            'voice_to_command = natural_language_commander.voice_to_command:main',
            'open_yolo_detector = natural_language_commander.open_yolo_detector:main',
        ],
    },
)
