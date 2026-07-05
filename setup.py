from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'anti_uav_system'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Ollie Larkins',
    maintainer_email='ollielarkins@hotmail.com',
    description='Anti-UAV detection, tracking, and ballistics system',
    license='MIT',
    entry_points={
        'console_scripts': [
            # nodes registered here as they are built:
            # 'yolo_node = anti_uav_system.nodes.yolo_node:main',
            # 'tracker_node = anti_uav_system.nodes.tracker_node:main',
            # 'ballistics_node = anti_uav_system.nodes.ballistics_node:main',
        ],
    },
)
