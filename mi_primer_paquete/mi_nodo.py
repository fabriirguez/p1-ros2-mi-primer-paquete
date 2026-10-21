from rcl_interfaces.msg import SetParametersResult
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_msgs.msg import String


class MiNodo(Node):
    def __init__(self):
        super().__init__('mi_nodo')

        self.publisher_ = self.create_publisher(String, 'saludo', 10)
        self.contador = 0

        self.declare_parameter('frecuencia_hz', 1.0)
        frecuencia = self.get_parameter('frecuencia_hz').value

        if not 0.1 <= frecuencia <= 20.0:
            raise ValueError(
                'frecuencia_hz debe estar entre 0.1 y 20.0 Hz'
            )

        self.timer = self.create_timer(
            1.0 / frecuencia, self.timer_callback
        )

        self.add_on_set_parameters_callback(self.validar_parametros)
        self.add_post_set_parameters_callback(self.aplicar_parametros)

    def validar_parametros(self, parametros):
        for parametro in parametros:
            if parametro.name == 'frecuencia_hz':
                if parametro.type_ != Parameter.Type.DOUBLE:
                    return SetParametersResult(
                        successful=False,
                        reason='Usa un decimal, por ejemplo 2.0'
                    )

                if not 0.1 <= parametro.value <= 20.0:
                    return SetParametersResult(
                        successful=False,
                        reason='La frecuencia debe estar entre 0.1 y 20.0 Hz'
                    )

        return SetParametersResult(successful=True)

    def aplicar_parametros(self, parametros):
        for parametro in parametros:
            if parametro.name == 'frecuencia_hz':
                frecuencia = self.get_parameter('frecuencia_hz').value

                self.timer.timer_period_ns = round(
                    1_000_000_000 / frecuencia
                )
                self.timer.reset()

                self.get_logger().info(
                    f'Frecuencia actualizada: {frecuencia} Hz'
                )

    def timer_callback(self):
        msg = String()
        msg.data = (
            f'Soy Fabricio y este es mi primer nodo. '
            f'Mensaje numero {self.contador}'
        )

        self.publisher_.publish(msg)
        self.get_logger().info(f'Publicando: "{msg.data}"')
        self.contador += 1


def main(args=None):
    rclpy.init(args=args)
    nodo = MiNodo()

    try:
        rclpy.spin(nodo)
    except KeyboardInterrupt:
        pass
    finally:
        nodo.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
