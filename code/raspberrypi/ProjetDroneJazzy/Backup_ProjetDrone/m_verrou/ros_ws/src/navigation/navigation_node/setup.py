from setuptools import setup

package_name = 'navigation_node'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
    maintainer_email='user@todo.todo',
    description='Navigation automatique bateau',
    license='TODO',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'navigation = navigation_node.navigation_verrou:main',
        ],
    },
)
