import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import serial
import struct


class Bridge_manette(Node):
    def __init__(self):
        super().__init__('bridge_manette')

        # Publisher /boussole  → sensor_msgs/Imu (orientation remplie)
        self.publisher_boussole = self.create_publisher(Imu, '/boussole', 10)

        # Publisher /inclinometre → sensor_msgs/Imu (angular_velocity remplie)
        self.publisher_inclinometre = self.create_publisher(Imu, '/inclinometre', 10)

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
            if start != 0x52 or frame_type != 0x02:
                self.get_logger().warn(
                    f"Trame ignorée : start={hex(start)} type={hex(frame_type)}"
                )
                return

            # 7 floats × 4 octets = 28 octets de payload
            if length != 0x1C or len(trame) < 31:
                self.get_logger().warn(
                    f"Trame IMU malformée : length={hex(length)} taille={len(trame)}"
                )
                return

            # Décodage 7 × float32 little-endian
            ox, oy, oz, ow, avx, avy, avz = struct.unpack('<fffffff', trame[3:31])

            self.get_logger().info(
                f"IMU décodé → orientation=({ox:.3f},{oy:.3f},{oz:.3f},{ow:.3f}) "
                f"angular_vel=({avx:.3f},{avy:.3f},{avz:.3f})"
            )

            now = self.get_clock().now().to_msg()

            # --- /boussole : orientation remplie ---
            boussole_msg = Imu()
            boussole_msg.header.stamp    = now
            boussole_msg.header.frame_id = "imu"

            boussole_msg.orientation.x = float(ox)
            boussole_msg.orientation.y = float(oy)
            boussole_msg.orientation.z = float(oz)
            boussole_msg.orientation.w = float(ow)

            # Covariance orientation connue (reprise de /imu/data)
            boussole_msg.orientation_covariance = [
                0.05, 0.0, 0.0,
                0.0, 0.05, 0.0,
                0.0, 0.0, 0.05
            ]
            # Champs non transmis → covariance -1 (indique "non disponible")
            boussole_msg.angular_velocity_covariance    = [-1.0] + [0.0] * 8
            boussole_msg.linear_acceleration_covariance = [-1.0] + [0.0] * 8

            self.publisher_boussole.publish(boussole_msg)
            self.get_logger().info(
                f"Publié sur /boussole → orientation=({ox:.3f},{oy:.3f},{oz:.3f},{ow:.3f})"
            )

            # --- /inclinometre : angular_velocity remplie ---
            inclinometre_msg = Imu()
            inclinometre_msg.header.stamp    = now
            inclinometre_msg.header.frame_id = "imu"

            inclinometre_msg.angular_velocity.x = float(avx)
            inclinometre_msg.angular_velocity.y = float(avy)
            inclinometre_msg.angular_velocity.z = float(avz)

            # Covariance angular_velocity connue (reprise de /imu/data)
            inclinometre_msg.angular_velocity_covariance = [
                0.02, 0.0, 0.0,
                0.0, 0.02, 0.0,
                0.0, 0.0, 0.02
            ]
            # Champs non transmis → covariance -1
            inclinometre_msg.orientation_covariance         = [-1.0] + [0.0] * 8
            inclinometre_msg.linear_acceleration_covariance = [-1.0] + [0.0] * 8

            self.publisher_inclinometre.publish(inclinometre_msg)
            self.get_logger().info(
                f"Publié sur /inclinometre → angular_vel=({avx:.3f},{avy:.3f},{avz:.3f})"
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
