from setuptools import find_packages, setup

package_name = 'mi_primer_paquete'

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
    maintainer='Fabricio Andree Rodriguez',
    maintainer_email='160241549+fabriirguez@users.noreply.github.com',
    description=(
        'P1 ROS 2: publicador /saludo y contador /contador con servicio '
        'de reinicio, parametro umbral y QoS TRANSIENT_LOCAL'
    ),
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'mi_nodo = mi_primer_paquete.mi_nodo:main',
            'contador_nodo = mi_primer_paquete.contador_nodo:main',
        ],
    },
)
