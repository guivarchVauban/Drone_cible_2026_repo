import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy, Imu, NavSatFix
from std_msgs.msg import String
import serial
import struct
import json
import time


class Bridge_manette(Node):

    def __init__(self):
        super().__init__('bridge_manette')

        # --- Publishers ---
        self.publisher_boussole     = self.create_publisher(Imu, '/boussole', 10)
        self.publisher_inclinometre = self.create_publisher(Imu, '/inclinometre', 10)
        self.publisher_gps          = self.create_publisher(NavSatFix, '/gps', 10)
        self.publisher_rectangle    = self.create_publisher(String, '/rectangle', 10)

        # --- Subscriber joystick ---
        self.subscription = self.create_subscription(
            Joy,
            '/joy',
            self.joy_callback,
            10
        )

        # --- UART ---
        try:
            self.ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.1)
            self.get_logger().info("UART ouvert avec succès")
        except serial.SerialException as e:
            self.get_logger().error(f"Erreur ouverture UART: {e}")
            self.ser = None

        # --- Anti-spam LoRa ---
        self.last_mapped_values = None
        self.last_change_time   = None

        # --- Timer lecture série ---
        self.timer = self.create_timer(0.01, self.read_serial)

    # ------------------------------------------------------------------ #
    # JOYSTICK → TRAME TX
    # ------------------------------------------------------------------ #
    def joy_callback(self, msg):
        x0, x1 = msg.axes[:2]

        x0_mapped = int((x0 + 1) * 127.5)
        x1_mapped = int(x1 * 10 + 10)

        current_values = (x0_mapped, x1_mapped)
        now = time.time()

        # Mise à jour du timestamp si les valeurs ont changé
        if current_values != self.last_mapped_values:
            self.last_mapped_values = current_values
            self.last_change_time   = now

        # Silence si stable depuis >= 1 seconde
        if (now - self.last_change_time) >= 1.0:
            self.get_logger().debug("Valeurs stables depuis 1s → envoi LoRa suspendu")
            return

        frame = bytearray([
            0x52,
            0x08,
            0x02,
            x0_mapped,
            x1_mapped
        ])

        self.get_logger().info(f"Trame TX: {[hex(b) for b in frame]}")

        if self.ser and self.ser.is_open:
            payload_hex = frame.hex()
            cmd = f"AT+SEND=0,{payload_hex},0,0\r\n"
            self.ser.write(cmd.encode())

    # ------------------------------------------------------------------ #
    # LECTURE UART
    # ------------------------------------------------------------------ #
    def read_serial(self):
        if self.ser is None:
            return
        try:
            if self.ser.in_waiting == 0:
                return

            line = self.ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                return

            self.get_logger().info(f"RAW reçu: '{line}'")

            if "HEX:" in line:
                self._parse_hex_closed(line)

        except Exception as e:
            self.get_logger().warn(f"Erreur lecture série : {e}")

    # ------------------------------------------------------------------ #
    # PARSER HEX
    # ------------------------------------------------------------------ #
    def _parse_hex_closed(self, line):
        try:
            hex_part = line.split("HEX:")[1].replace(")", "").strip()
            trame = bytes([int(h, 16) for h in hex_part.split()])
        except Exception as e:
            self.get_logger().warn(f"Erreur décodage HEX : {e}")
            return

        self.get_logger().info(f"Trame RX : {[hex(b) for b in trame]}")

        if len(trame) < 3:
            return

        start      = trame[0]
        frame_type = trame[1]
        length     = trame[2]

        if start != 0x52:
            self.get_logger().warn(f"Start byte inattendu : {hex(start)}")
            return

        if frame_type == 0x01:
            self._handle_gps(trame, length)
        elif frame_type == 0x02:
            self._handle_imu(trame, length)
        elif frame_type == 0x03:
            self._handle_rectangle(trame)
        else:
            self.get_logger().warn(f"Type de trame inconnu : {hex(frame_type)}")

    # ------------------------------------------------------------------ #
    # GPS
    # ------------------------------------------------------------------ #
    def _handle_gps(self, trame, length):
        if length != 0x08 or len(trame) < 11:
            return

        lat = struct.unpack('<f', trame[3:7])[0]
        lon = struct.unpack('<f', trame[7:11])[0]

        msg = NavSatFix()
        msg.header.stamp    = self.get_clock().now().to_msg()
        msg.header.frame_id = "gps"
        msg.latitude        = float(lat)
        msg.longitude       = float(lon)
        msg.altitude        = 0.0

        self.publisher_gps.publish(msg)
        self.get_logger().info(f"GPS publié : lat={lat:.6f} lon={lon:.6f}")

    # ------------------------------------------------------------------ #
    # IMU
    # ------------------------------------------------------------------ #
    def _handle_imu(self, trame, length):
        if length != 0x1C or len(trame) < 31:
            self.get_logger().warn(f"Trame IMU malformée : length={hex(length)} taille={len(trame)}")
            return

        ox, oy, oz, ow, avx, avy, avz = struct.unpack('<fffffff', trame[3:31])

        now = self.get_clock().now().to_msg()

        # --- /boussole : orientation remplie ---
        boussole_msg = Imu()
        boussole_msg.header.stamp    = now
        boussole_msg.header.frame_id = "imu"
        boussole_msg.orientation.x   = float(ox)
        boussole_msg.orientation.y   = float(oy)
        boussole_msg.orientation.z   = float(oz)
        boussole_msg.orientation.w   = float(ow)
        boussole_msg.orientation_covariance = [
            0.05, 0.0, 0.0,
            0.0, 0.05, 0.0,
            0.0, 0.0, 0.05
        ]
        boussole_msg.angular_velocity_covariance    = [-1.0] + [0.0] * 8
        boussole_msg.linear_acceleration_covariance = [-1.0] + [0.0] * 8

        self.publisher_boussole.publish(boussole_msg)
        self.get_logger().info(
            f"Publié /boussole → orientation=({ox:.3f},{oy:.3f},{oz:.3f},{ow:.3f})"
        )

        # --- /inclinometre : angular_velocity remplie ---
        inclinometre_msg = Imu()
        inclinometre_msg.header.stamp    = now
        inclinometre_msg.header.frame_id = "imu"
        inclinometre_msg.angular_velocity.x = float(avx)
        inclinometre_msg.angular_velocity.y = float(avy)
        inclinometre_msg.angular_velocity.z = float(avz)
        inclinometre_msg.angular_velocity_covariance = [
            0.02, 0.0, 0.0,
            0.0, 0.02, 0.0,
            0.0, 0.0, 0.02
        ]
        inclinometre_msg.orientation_covariance         = [-1.0] + [0.0] * 8
        inclinometre_msg.linear_acceleration_covariance = [-1.0] + [0.0] * 8

        self.publisher_inclinometre.publish(inclinometre_msg)
        self.get_logger().info(
            f"Publié /inclinometre → angular_vel=({avx:.3f},{avy:.3f},{avz:.3f})"
        )

    # ------------------------------------------------------------------ #
    # RECTANGLE
    # ------------------------------------------------------------------ #
    def _handle_rectangle(self, trame):
        nb = trame[2]
        detections = []

        for i in range(nb):
            offset = 3 + i * 8
            if offset + 8 > len(trame):
                break

            x = trame[offset]     | (trame[offset + 1] << 8)
            y = trame[offset + 2] | (trame[offset + 3] << 8)
            w = trame[offset + 4] | (trame[offset + 5] << 8)
            h = trame[offset + 6] | (trame[offset + 7] << 8)

            detections.append({"x": x, "y": y, "width": w, "height": h})

        msg = String()
        msg.data = json.dumps(detections)
        self.publisher_rectangle.publish(msg)
        self.get_logger().info(f"Rectangle publié : {detections}")

    # ------------------------------------------------------------------ #
    # CLEAN EXIT
    # ------------------------------------------------------------------ #
    def destroy_node(self):
        if self.ser:
            self.ser.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = Bridge_manette()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
