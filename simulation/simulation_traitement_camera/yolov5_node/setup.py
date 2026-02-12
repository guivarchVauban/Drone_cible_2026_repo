from setuptools import setup

package_name = 'boat_detector'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    install_requires=['setuptools', 'torch', 'numpy<2', 'opencv-python', 'pandas'],
    zip_safe=True,
    author='Nolan',
    description='Boat detection node with YOLOv5',
    entry_points={
        'console_scripts': [
            'yolo_node = boat_detector.yolo_node:main',
        ],
    },
)