import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu

import math
import board
import busio

import adafruit_fxos8700
import adafruit_fxas21002c


def euler_to_quaternion(roll, pitch, yaw):
    qx = math.sin(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) - math.cos(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
    qy = math.cos(roll/2) * math.sin(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.cos(pitch/2) * math.sin(yaw/2)
    qz = math.cos(roll/2) * math.cos(pitch/2) * math.sin(yaw/2) - math.sin(roll/2) * math.sin(pitch/2) * math.cos(yaw/2)
    qw = math.cos(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
    return qx, qy, qz, qw


class ImuNode(Node):

    def __init__(self):
        super().__init__('imu_node')

        self.publisher_ = self.create_publisher(Imu, '/imu/data', 10)

        # I2C
        i2c = busio.I2C(board.SCL, board.SDA)

        # Capteurs
        self.accel_mag = adafruit_fxos8700.FXOS8700(i2c)
        self.gyro = adafruit_fxas21002c.FXAS21002C(i2c)

        # Timer 100 Hz
        self.timer = self.create_timer(0.01, self.publish_imu)

        self.get_logger().info("IMU 9DOF Node démarré")

    def publish_imu(self):

        msg = Imu()

        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"

        # =========================
        # ACCELERATION
        # =========================
        ax, ay, az = self.accel_mag.accelerometer
        msg.linear_acceleration.x = ax
        msg.linear_acceleration.y = ay
        msg.linear_acceleration.z = az

        # =========================
        # GYROSCOPE (rad/s)
        # =========================
        gx, gy, gz = self.gyro.gyroscope

        msg.angular_velocity.x = gx
        msg.angular_velocity.y = gy
        msg.angular_velocity.z = gz

        # =========================
        # MAGNETOMETRE → YAW
        # =========================
        mx, my, mz = self.accel_mag.magnetometer

        yaw = math.atan2(my, mx)

        # =========================
        # ORIENTATION
        # =========================
        roll = 0.0
        pitch = 0.0

        qx, qy, qz, qw = euler_to_quaternion(roll, pitch, yaw)

        msg.orientation.x = qx
        msg.orientation.y = qy
        msg.orientation.z = qz
        msg.orientation.w = qw

        # =========================
        # COVARIANCES (IMPORTANT EKF)
        # =========================
        msg.orientation_covariance[0] = 0.05
        msg.orientation_covariance[4] = 0.05
        msg.orientation_covariance[8] = 0.1

        msg.angular_velocity_covariance[0] = 0.02
        msg.angular_velocity_covariance[4] = 0.02
        msg.angular_velocity_covariance[8] = 0.02

        msg.linear_acceleration_covariance[0] = 0.1
        msg.linear_acceleration_covariance[4] = 0.1
        msg.linear_acceleration_covariance[8] = 0.1

        self.publisher_.publish(msg)


def main():
    rclpy.init()
    node = ImuNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
