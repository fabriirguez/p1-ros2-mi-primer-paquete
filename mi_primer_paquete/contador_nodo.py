from rcl_interfaces.msg import SetParametersResult
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import (
    DurabilityPolicy,
    QoSProfile,
    ReliabilityPolicy
)
from std_msgs.msg import Int32, String
from std_srvs.srv import Trigger


class ContadorNodo(Node):

    def __init__(self):
        super().__init__('contador_nodo')

        self.contador = 0
        self.aviso_emitido = False

        # R4: parametro dinamico
        self.declare_parameter('umbral', 10)
        self.add_on_set_parameters_callback(
            self.validar_parametros
        )
        self.add_post_set_parameters_callback(
            self.aplicar_parametros
        )

        # R2: recibir saludos
        self.suscriptor = self.create_subscription(
            String, '/saludo', self.recibir_saludo, 10
        )

        # R5: QoS del contador
        qos_contador = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL
        )

        self.publicador = self.create_publisher(
            Int32,
            '/contador',
            qos_contador
        )

        # R3: servicio de reinicio
        self.servicio = self.create_service(
            Trigger,
            'reiniciar_contador',
            self.reiniciar_contador
        )

        self.get_logger().info('Contador iniciado')

    def validar_parametros(self, parametros):
        for parametro in parametros:
            if parametro.name == 'umbral':
                if (
                    parametro.type_ != Parameter.Type.INTEGER
                    or parametro.value < 1
                ):
                    return SetParametersResult(
                        successful=False,
                        reason='El umbral debe ser un entero positivo'
                    )

        return SetParametersResult(successful=True)

    def aplicar_parametros(self, parametros):
        for parametro in parametros:
            if parametro.name == 'umbral':
                self.aviso_emitido = False
                self.get_logger().info(
                    f'Umbral actualizado a {parametro.value}'
                )

    def recibir_saludo(self, msg):
        self.contador += 1

        resultado = Int32()
        resultado.data = self.contador
        self.publicador.publish(resultado)

        self.get_logger().info(
            f'Recibido: {msg.data} | Total: {self.contador}'
        )

        umbral = self.get_parameter('umbral').value

        if self.contador >= umbral and not self.aviso_emitido:
            self.get_logger().warn(
                f'Umbral alcanzado: {self.contador} mensajes'
            )
            self.aviso_emitido = True

    def reiniciar_contador(self, request, response):
        self.contador = 0
        self.aviso_emitido = False

        mensaje = Int32()
        mensaje.data = 0
        self.publicador.publish(mensaje)

        response.success = True
        response.message = 'Contador reiniciado correctamente'

        self.get_logger().info(response.message)
        return response


def main(args=None):
    rclpy.init(args=args)
    nodo = ContadorNodo()

    try:
        rclpy.spin(nodo)
    except KeyboardInterrupt:
        pass
    finally:
        nodo.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
