import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import String
import serial
import json

class Bridge_manette(Node):
    def __init__(self):
        super().__init__('bridge_manette')

        # Subscription /joy
        self.subscription = self.create_subscription(
            Joy,
            '/joy',
            self.listener_callback,
            10)

        # Publisher /rectangle
        self.publisher_rectangle = self.create_publisher(String, '/rectangle', 10)

        try:
            self.ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.1)
            self.get_logger().info("UART ouvert avec succès")
        except serial.SerialException as e:
            self.get_logger().error(f"Erreur ouverture UART: {e}")
            self.ser = None

        # Timer lecture série
        self.timer = self.create_timer(0.01, self.read_serial)

    def listener_callback(self, msg):
        x0, x1 = msg.axes[:2]
        x0_mapped = int((x0+1)*127.5)
        x1_mapped = int(x1*10+10)
        frame = bytearray([
            0x52,
            0x08,
            0x02,
            x0_mapped,
            x1_mapped
        ])
        self.get_logger().info(f"Trame: {[hex(b) for b in frame]}")
        if self.ser and self.ser.is_open:
            payload_hex = frame.hex()
            cmd = f"AT+SEND=0,{payload_hex},0,0\r\n"
            self.get_logger().info(f"Commande LoRa: {cmd.strip()}")
            self.ser.write(cmd.encode())

    def read_serial(self):
        if self.ser is None:
            return

        try:
            if self.ser.in_waiting == 0:
                return

            line = self.ser.readline().decode("utf-8", errors="ignore").strip()

            if not line:
                return

            if "Data: (HEX:)" not in line:
                return

            self.get_logger().info(f"Reçu brut : {line}")

            hex_part = line.split("HEX:)")[1].strip()
            hex_values = hex_part.split()
            trame = bytes([int(h, 16) for h in hex_values])

            self.get_logger().info(f"Trame reçue : {[hex(b) for b in trame]}")

            if len(trame) < 3:
                return

            start = trame[0]
            frame_type = trame[1]
            nb = trame[2]

            if start != 0x52 or frame_type != 0x03:
                self.get_logger().warn(f"Trame inconnue : start={hex(start)} type={hex(frame_type)}")
                return

            self.get_logger().info(f"Nombre de détections : {nb}")

            detections = []

            for i in range(nb):
                offset = 3 + i * 8
                if offset + 8 > len(trame):
                    break

                x = trame[offset] | (trame[offset+1] << 8)
                y = trame[offset+2] | (trame[offset+3] << 8)
                w = trame[offset+4] | (trame[offset+5] << 8)
                h = trame[offset+6] | (trame[offset+7] << 8)

                self.get_logger().info(
                    f"  Détection {i+1} -> x={x} y={y} width={w} height={h}"
                )

                detections.append({
                    "x": x,
                    "y": y,
                    "width": w,
                    "height": h
                })

            # Publication sur /rectangle
            msg = String()
            msg.data = json.dumps(detections)
            self.publisher_rectangle.publish(msg)
            self.get_logger().info(f"Publié sur /rectangle : {msg.data}")

        except Exception as e:
            self.get_logger().warn(f"Erreur lecture série : {e}")

    def destroy_node(self):
        if self.ser is not None and self.ser.is_open:
            self.ser.close()
            self.get_logger().info("UART fermé")
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    bridge_manette = Bridge_manette()
    try:
        rclpy.spin(bridge_manette)
    except KeyboardInterrupt:
        pass
    bridge_manette.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
