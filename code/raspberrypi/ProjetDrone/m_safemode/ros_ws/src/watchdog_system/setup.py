from setuptools import setup

package_name = 'watchdog_system'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='root',
    maintainer_email='root@todo.todo',
    description='ROS2 Watchdog System',
    license='TODO',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'watchdog_node = watchdog_system.watchdog_node:main',
        ],
    },
)
