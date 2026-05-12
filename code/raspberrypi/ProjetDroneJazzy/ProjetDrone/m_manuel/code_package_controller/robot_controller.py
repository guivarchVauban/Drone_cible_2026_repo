import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo  # <--- AJOUTÉ : Pour gérer les servos
import RPi.GPIO as GPIO

class RobotController(Node):
    def __init__(self):
        super().__init__('robot_controller')
        
        # ==================== Configuration GPIO ====================
        self.Motor0_A, self.Motor0_B = 18, 17
        self.Motor1_A, self.Motor1_B = 22, 27
        self.pins = [self.Motor0_A, self.Motor0_B, self.Motor1_A, self.Motor1_B]
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pins, GPIO.OUT, initial=GPIO.LOW)

        # ==================== Configuration PCA9685 ====================
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.pca = PCA9685(self.i2c)
        self.pca.frequency = 50
        # --- AJOUTÉ : Configuration du Servo de direction ---
        self.servo_direction = servo.Servo(self.pca.channels[0])
	#self.servo_direction = servo.Servo(self.pca.channels[0], min_pulse=1000, max_pulse=2000)
        # Canaux PWM pour Enable (Vitesse moteurs DC)
        self.pwm_m0 = self.pca.channels[5]
        self.pwm_m1 = self.pca.channels[4]

        self.subscription = self.create_subscription(Twist, 'cmd_vel', self.listener_callback, 10)
        self.get_logger().info('Contrôleur prêt : Moteurs DC + Servo Direction (CH0)')

    def set_motors(self, speed):
        duty = int(abs(speed) * 65535)
        if speed > 0:
            GPIO.output(self.Motor0_A, GPIO.HIGH); GPIO.output(self.Motor0_B, GPIO.LOW)
            GPIO.output(self.Motor1_A, GPIO.HIGH); GPIO.output(self.Motor1_B, GPIO.LOW)
        elif speed < 0:
            GPIO.output(self.Motor0_A, GPIO.LOW); GPIO.output(self.Motor0_B, GPIO.HIGH)
            GPIO.output(self.Motor1_A, GPIO.LOW); GPIO.output(self.Motor1_B, GPIO.HIGH)
        else:
            GPIO.output(self.pins, GPIO.LOW)
            duty = 0
        self.pwm_m0.duty_cycle = duty
        self.pwm_m1.duty_cycle = duty

    def listener_callback(self, msg):
        # 1. Gestion des moteurs DC (Vitesse)
        self.set_motors(msg.linear.x)

        # 2. --- AJOUTÉ : Gestion du Servo de direction ---
        # msg.angular.z est positif pour la gauche, négatif pour la droite
        # On mappe -1.0/1.0 sur un angle de 45° à 135° (Centre à 90°)
        angle = 90 + (msg.angular.z * 45)
        
        # Sécurité : On bride l'angle entre 0 et 180 pour ne pas abîmer le servo
        angle = max(0.0, min(180.0, angle))
        
        self.servo_direction.angle = angle
        
        # Log optionnel pour voir ce qui se passe
        # self.get_logger().info(f'Vitesse: {msg.linear.x} | Angle: {angle}')

    def stop_all(self):
        self.pwm_m0.duty_cycle = 0
        self.pwm_m1.duty_cycle = 0
        self.servo_direction.angle = 90 # Remet les roues droites avant de couper
        GPIO.output(self.pins, GPIO.LOW)
        GPIO.cleanup()

def main(args=None):
    rclpy.init(args=args)
    node = RobotController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.stop_all()
    finally:
        node.destroy_node()
        rclpy.shutdown()
