import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from geometry_msgs.msg import Quaternion
from smbus2 import SMBus
import math

FXOS8700_ADDR  = 0x1F
FXAS21002C_ADDR = 0x21
MAG_DECLINATION = math.radians(-2.0)

# Sensibilités
ACCEL_SCALE = 9.81 / 4096.0          # ±2g, 14 bits → m/s²
GYRO_SCALE  = 0.0078125 * math.pi / 180.0  # ±250°/s → rad/s


def read_raw(bus, addr, reg):
    """Lecture 16 bits signé standard"""
    high = bus.read_byte_data(addr, reg)
    low  = bus.read_byte_data(addr, reg + 1)
    val  = (high << 8) | low
    if val >= 0x8000:
        val -= 0x10000
    return val


def read_accel(bus, addr, reg):
    """Lecture 14 bits signé pour l'accéléromètre FXOS8700"""
    high = bus.read_byte_data(addr, reg)
    low  = bus.read_byte_data(addr, reg + 1)
    val  = (high << 8) | low
    val >>= 2          # données alignées à gauche sur 16 bits, utiles sur 14
    if val >= 0x2000:  # 2^13
        val -= 0x4000  # signe sur 14 bits
    return val


class ImuNode(Node):

    def __init__(self):
        super().__init__('imu_node')
        self.pub_imu = self.create_publisher(Imu, '/imu/data', 10)
        self.bus = SMBus(1)

        # Init FXOS8700 (accel + mag)
        self.bus.write_byte_data(FXOS8700_ADDR, 0x2A, 0x00)  # standby
        self.bus.write_byte_data(FXOS8700_ADDR, 0x5B, 0x1F)  # hybrid
        self.bus.write_byte_data(FXOS8700_ADDR, 0x5C, 0x20)  # oversampling
        self.bus.write_byte_data(FXOS8700_ADDR, 0x2A, 0x0D)  # active

        # Init FXAS21002C (gyro)
        self.bus.write_byte_data(FXAS21002C_ADDR, 0x13, 0x00)  # standby
        self.bus.write_byte_data(FXAS21002C_ADDR, 0x0D, 0x0E)  # ±250°/s
        self.bus.write_byte_data(FXAS21002C_ADDR, 0x13, 0x02)  # active

        self.timer = self.create_timer(2.0, self.publish_data)
        self.get_logger().info("IMU Node démarré")

    def publish_data(self):
        now = self.get_clock().now().to_msg()

        # Accéléromètre (14 bits)
        ax = read_accel(self.bus, FXOS8700_ADDR, 0x01) * ACCEL_SCALE
        ay = read_accel(self.bus, FXOS8700_ADDR, 0x03) * ACCEL_SCALE
        az = read_accel(self.bus, FXOS8700_ADDR, 0x05) * ACCEL_SCALE

        # Magnétomètre (16 bits)
        mx = read_raw(self.bus, FXOS8700_ADDR, 0x33)
        my = read_raw(self.bus, FXOS8700_ADDR, 0x35)
        mz = read_raw(self.bus, FXOS8700_ADDR, 0x37)

        # Gyroscope (16 bits)
        gx = read_raw(self.bus, FXAS21002C_ADDR, 0x01) * GYRO_SCALE
        gy = read_raw(self.bus, FXAS21002C_ADDR, 0x03) * GYRO_SCALE
        gz = read_raw(self.bus, FXAS21002C_ADDR, 0x05) * GYRO_SCALE

        # Roll et Pitch depuis accéléromètre
        roll  = math.atan2(ay, az)
        pitch = math.atan2(-ax, math.sqrt(ay**2 + az**2))

        # Yaw avec compensation de tilt
        cos_r, sin_r = math.cos(roll),  math.sin(roll)
        cos_p, sin_p = math.cos(pitch), math.sin(pitch)
        mx_c =  mx * cos_p + mz * sin_p
        my_c =  mx * sin_r * sin_p + my * cos_r - mz * sin_r * cos_p
        yaw  = math.atan2(-my_c, mx_c) + MAG_DECLINATION
        yaw  = math.atan2(math.sin(yaw), math.cos(yaw))

        # Debug
        self.get_logger().info(
            f"az={az:.2f} m/s² | "
            f"roll={math.degrees(roll):.1f}° "
            f"pitch={math.degrees(pitch):.1f}° "
            f"yaw={math.degrees(yaw):.1f}°"
        )

        q = self.euler_to_quaternion(roll, pitch, yaw)

        msg = Imu()
        msg.header.stamp    = now
        msg.header.frame_id = "base_link"
        msg.orientation.x = q.x
        msg.orientation.y = q.y
        msg.orientation.z = q.z
        msg.orientation.w = q.w
        msg.orientation_covariance        = [0.05,0,0, 0,0.05,0, 0,0,0.05]
        msg.angular_velocity.x = gx
        msg.angular_velocity.y = gy
        msg.angular_velocity.z = gz
        msg.angular_velocity_covariance   = [0.02,0,0, 0,0.02,0, 0,0,0.02]
        msg.linear_acceleration.x = ax
        msg.linear_acceleration.y = ay
        msg.linear_acceleration.z = az
        msg.linear_acceleration_covariance = [0.1,0,0, 0,0.1,0, 0,0,0.1]

        self.pub_imu.publish(msg)

    def euler_to_quaternion(self, roll, pitch, yaw):
        q  = Quaternion()
        cy, sy = math.cos(yaw*0.5),   math.sin(yaw*0.5)
        cp, sp = math.cos(pitch*0.5), math.sin(pitch*0.5)
        cr, sr = math.cos(roll*0.5),  math.sin(roll*0.5)
        q.w = cr*cp*cy + sr*sp*sy
        q.x = sr*cp*cy - cr*sp*sy
        q.y = cr*sp*cy + sr*cp*sy
        q.z = cr*cp*sy - sr*sp*cy
        return q


def main(args=None):
    rclpy.init(args=args)
    node = ImuNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
