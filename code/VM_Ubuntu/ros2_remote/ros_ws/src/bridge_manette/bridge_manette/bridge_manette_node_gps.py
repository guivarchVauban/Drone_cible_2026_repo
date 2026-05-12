import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix
import serial
import struct


class Bridge_manette(Node):
    def __init__(self):
        super().__init__('bridge_manette')

        # Publisher /gps (NavSatFix)
        self.publisher_gps = self.create_publisher(NavSatFix, '/gps', 10)

        try:
            self.ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.1)
            self.get_logger().info("UART ouvert avec succès")
        except serial.SerialException as e:
            self.get_logger().error(f"Erreur ouverture UART: {e}")
            self.ser = None

        # Timer lecture série
        self.timer = self.create_timer(0.01, self.read_serial)

    def read_serial(self):
        if self.ser is None:
            return

        try:
            if self.ser.in_waiting == 0:
                return

            line = self.ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                return

            if "Data: (HEX:" not in line:
                return

            self.get_logger().info(f"Reçu brut : {line}")

            # Extraction des octets hex
            hex_part = line.split("HEX:")[1]
            hex_part = hex_part.replace(")", "").strip()
            hex_values = hex_part.split()
            trame = bytes([int(h, 16) for h in hex_values])

            self.get_logger().info(f"Trame reçue : {[hex(b) for b in trame]}")

            if len(trame) < 3:
                return

            start      = trame[0]
            frame_type = trame[1]
            length     = trame[2]

            # Vérification en-tête
            if start != 0x52 or frame_type != 0x01:
                self.get_logger().warn(
                    f"Trame ignorée : start={hex(start)} type={hex(frame_type)}"
                )
                return

            if length != 0x08 or len(trame) < 11:
                self.get_logger().warn(
                    f"Trame GPS malformée : length={hex(length)} taille={len(trame)}"
                )
                return

            # Décodage float32 little-endian
            lat = struct.unpack('<f', trame[3:7])[0]
            lon = struct.unpack('<f', trame[7:11])[0]

            self.get_logger().info(f"GPS décodé → lat={lat:.6f} lon={lon:.6f}")

            # Construction et publication du NavSatFix
            gps_msg = NavSatFix()
            gps_msg.header.stamp    = self.get_clock().now().to_msg()
            gps_msg.header.frame_id = "gps"

            gps_msg.status.status  = 0   # STATUS_FIX
            gps_msg.status.service = 1   # SERVICE_GPS

            gps_msg.latitude  = float(lat)
            gps_msg.longitude = float(lon)
            gps_msg.altitude  = 0.0      # non transmis dans cette trame

            gps_msg.position_covariance_type = NavSatFix.COVARIANCE_TYPE_UNKNOWN
            gps_msg.position_covariance      = [0.0] * 9

            self.publisher_gps.publish(gps_msg)
            self.get_logger().info(
                f"Publié sur /gps → lat={lat:.6f} lon={lon:.6f}"
            )

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
