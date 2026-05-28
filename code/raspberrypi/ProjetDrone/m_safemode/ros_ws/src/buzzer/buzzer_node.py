import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from gpiozero import Buzzer
import threading
import time

BUZZER_PIN = 23
EMERGENCY_MODE = "3"

buzzer = Buzzer(BUZZER_PIN)
_stop_event = threading.Event()


def sirene():
    _stop_event.clear()
    print("SIRENE ACTIVE")
    try:
        while not _stop_event.is_set():
            for duree in [0.35, 0.25, 0.15, 0.08, 0.05]:
                if _stop_event.is_set():
                    break
                buzzer.on()
                time.sleep(duree)
                buzzer.off()
                time.sleep(0.03)
            if _stop_event.is_set():
                break
            for duree in [0.05, 0.08, 0.15, 0.25, 0.35]:
                if _stop_event.is_set():
                    break
                buzzer.on()
                time.sleep(duree)
                buzzer.off()
                time.sleep(0.03)
    finally:
        buzzer.off()
        print("Sirene arretee")


def stopper_sirene():
    _stop_event.set()
    buzzer.off()


class BuzzerNode(Node):
    def __init__(self):
        super().__init__("buzzer_node")
        self._sirene_thread = None
        self._mode_actuel = None
        self.subscription = self.create_subscription(
            String,
            "/robot_mode",
            self.callback_mode,
            10
        )
        self.get_logger().info("Buzzer node demarre")

    def callback_mode(self, msg):
        mode = msg.data
        if mode == self._mode_actuel:
            return
        self._mode_actuel = mode
        self.get_logger().info("Mode recu : " + mode)
        if mode == EMERGENCY_MODE:
            self.get_logger().warn("ARRET URGENCE")
            self._demarrer_sirene()
        else:
            if self._sirene_active():
                stopper_sirene()

    def _demarrer_sirene(self):
        if not self._sirene_active():
            _stop_event.clear()
            self._sirene_thread = threading.Thread(target=sirene, daemon=True)
            self._sirene_thread.start()

    def _sirene_active(self):
        return self._sirene_thread is not None and self._sirene_thread.is_alive()

    def destroy_node(self):
        stopper_sirene()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = BuzzerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        stopper_sirene()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
