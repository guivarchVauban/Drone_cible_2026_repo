import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
import serial


class Bridge_manette(Node):

    def __init__(self):
        super().__init__('bridge_manette')

        self.subscription = self.create_subscription(
            Joy,
            '/joy',
            self.listener_callback,
            10)

        try:
            self.ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.1)
            self.get_logger().info("UART ouvert avec succès")
        except serial.SerialException as e:
            self.get_logger().error(f"Erreur ouverture UART: {e}")
            self.ser = None


    def listener_callback(self, msg):

        x0, x1 = msg.axes[:2]

        x0_mapped = int((x0+1)*127.5)
        x1_mapped = int(x1*10+10)

        frame = bytearray([
            0x52,      # Start
            0x08,      # Type
            0x02,      # Length
            x0_mapped, # Payload[0]
            x1_mapped  # Payload[1]
        ])

        self.get_logger().info(f"Trame: {[hex(b) for b in frame]}")

        if self.ser and self.ser.is_open:

            # conversion en hex
            payload_hex = frame.hex()

            # construction commande AT
            cmd = f"AT+SEND=0,{payload_hex},0,0\r\n"

            self.get_logger().info(f"Commande LoRa: {cmd.strip()}")

            # envoi
            self.ser.write(cmd.encode())


def main(args=None):

    rclpy.init(args=args)
    bridge_manette = Bridge_manette()

    try:
        rclpy.spin(bridge_manette)
    except KeyboardInterrupt:
        pass

    if bridge_manette.ser and bridge_manette.ser.is_open:
        bridge_manette.ser.close()
        bridge_manette.get_logger().info("UART fermé")

    bridge_manette.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
