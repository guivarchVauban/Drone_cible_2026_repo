import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, MagneticField
import smbus2
import math
import time

class IMUPublisher(Node):
    def __init__(self, calib_samples=200):
        super().__init__('imu_publisher')

        # Publishers ROS 2
#        self.imu_pub = self.create_publisher(Imu, 'imu/data_raw', 10)
        self.imu_pub = self.create_publisher(Imu, 'imu/rotation', 10)
#        self.mag_pub = self.create_publisher(MagneticField, 'imu/mag', 10)
        self.mag_pub = self.create_publisher(MagneticField, 'imu/boussole', 10)

        # Bus I2C
        self.bus = smbus2.SMBus(1)
        self.ADDR_ACCEL_MAG = 0x1F
        self.ADDR_GYRO = 0x21

        # Init capteurs
        self.init_fxos()
        self.init_fxas()

        # --------- CALIBRATION ---------
        self.accel_offset = [0.0, 0.0, 0.0]
        self.gyro_offset = [0.0, 0.0, 0.0]
        self.calibrate(calib_samples)

        # Timer 2 Hz (0.5 s)
        self.timer = self.create_timer(0.5, self.timer_callback)

    # -------------------------
    # Initialisation FXOS8700
    # -------------------------
    def init_fxos(self):
        FXOS_CTRL_REG1 = 0x2A
        self.bus.write_byte_data(self.ADDR_ACCEL_MAG, FXOS_CTRL_REG1, 0x01)

    # -------------------------
    # Initialisation FXAS21002
    # -------------------------
    def init_fxas(self):
        GYRO_CTRL_REG1 = 0x13
        self.bus.write_byte_data(self.ADDR_GYRO, GYRO_CTRL_REG1, 0x0E)

    # -------------------------
    # Lecture Accél + Mag
    # -------------------------
    def read_accel_mag(self):
        data = self.bus.read_i2c_block_data(self.ADDR_ACCEL_MAG, 0x01, 12)

        # Accélération 14-bit
        accel = []
        for i in range(0, 6, 2):
            raw = ((data[i] << 8) | data[i+1]) >> 2
            if raw > 8191:
                raw -= 16384
            accel.append(raw / 4096.0)

        # Magnétomètre 16-bit
        mag = []
        for i in range(6, 12, 2):
            raw = (data[i] << 8) | data[i+1]
            if raw > 32767:
                raw -= 65536
            mag.append(raw * 0.1)  # approximation µT

        return accel, mag

    # -------------------------
    # Lecture Gyro
    # -------------------------
    def read_gyro(self):
        data = self.bus.read_i2c_block_data(self.ADDR_GYRO, 0x01, 6)
        gyro = []
        for i in range(0, 6, 2):
            raw = (data[i] << 8) | data[i+1]
            if raw > 32767:
                raw -= 65536
            gyro.append(raw / 16.4)  # 2000 dps
        return gyro

    # -------------------------
    # Calibration automatique
    # -------------------------
    def calibrate(self, samples=200):
        print("Calibration IMU… Ne pas bouger le capteur !")
        accel_sum = [0.0, 0.0, 0.0]
        gyro_sum = [0.0, 0.0, 0.0]

        for _ in range(samples):
            accel, _ = self.read_accel_mag()
            gyro = self.read_gyro()
            for i in range(3):
                accel_sum[i] += accel[i]
                gyro_sum[i] += gyro[i]
            time.sleep(0.01)  # 100 Hz lecture

        # Moyenne
        self.accel_offset = [s / samples for s in accel_sum]
        self.gyro_offset = [s / samples for s in gyro_sum]

        print(f"Offset Accel : {self.accel_offset}")
        print(f"Offset Gyro  : {self.gyro_offset}")
        print("Calibration terminée !")

    # -------------------------
    # Callback Timer
    # -------------------------
    def timer_callback(self):
        accel, mag = self.read_accel_mag()
        gyro = self.read_gyro()

        # Appliquer offset
        accel = [accel[i] - self.accel_offset[i] for i in range(3)]
        gyro = [gyro[i] - self.gyro_offset[i] for i in range(3)]

        # Publier Imu
        imu_msg = Imu()
        imu_msg.linear_acceleration.x = accel[0] * 9.80665
        imu_msg.linear_acceleration.y = accel[1] * 9.80665
        imu_msg.linear_acceleration.z = accel[2] * 9.80665
        imu_msg.angular_velocity.x = math.radians(gyro[0])
        imu_msg.angular_velocity.y = math.radians(gyro[1])
        imu_msg.angular_velocity.z = math.radians(gyro[2])
        self.imu_pub.publish(imu_msg)

        # Publier magnétomètre (brut)
        mag0 = mag[0]
        mag1 = mag[1]
        mag2 = mag[2]

        mag_msg = MagneticField()
        mag_msg.magnetic_field.x = mag[0] * 1e-6
        mag_msg.magnetic_field.y = mag[1] * 1e-6
        mag_msg.magnetic_field.z = mag[2] * 1e-6
        self.mag_pub.publish(mag_msg)

        # PRINT lisible
        print("\n------ Lecture IMU ------")
        print(f"Accélération (g) : X={accel[0]:.2f}, Y={accel[1]:.2f}, Z={accel[2]:.2f}")
        print(f"Gyroscope (°/s)   : X={gyro[0]:.2f}, Y={gyro[1]:.2f}, Z={gyro[2]:.2f}")
        print(f"Magnétomètre (µT) : X={mag[0]:.1f}, Y={mag[1]:.1f}, Z={mag[2]:.1f}")
        print("--------------------------")

def main(args=None):
    rclpy.init(args=args)
    node = IMUPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
