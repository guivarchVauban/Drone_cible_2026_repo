#!/usr/bin/env python3
import os
import sys
import rclpy
from rclpy.node import Node
from rclpy.context import Context
from std_msgs.msg import Int32
import subprocess
import time


# Supprime les messages rcutils/serdata sur stderr AVANT rclpy.init()
# en redirigeant stderr vers un filtre en temps réel
class StderrFilter:
    BLOCKED = (
        b'rcutils_set_error_state',
        b'rcutils_reset_error',
        b'serdata.cpp',
        b'error_handling.c',
        b'sequence size exceeds',
        b'>>>',
        b'<<<',
        b'XMLPARSER',
    )

    def __init__(self, real_stderr):
        self._real = real_stderr
        self._buf = b''

    def write(self, data):
        if isinstance(data, str):
            data = data.encode()
        self._buf += data
        while b'\n' in self._buf:
            line, self._buf = self._buf.split(b'\n', 1)
            if not any(p in line for p in self.BLOCKED):
                self._real.buffer.write(line + b'\n')
                self._real.buffer.flush()

    def flush(self):
        if self._buf and not any(p in self._buf for p in self.BLOCKED):
            self._real.buffer.write(self._buf)
            self._real.buffer.flush()
        self._buf = b''

    def fileno(self):
        return self._real.fileno()


# Installe le filtre avant tout import ROS
sys.stderr = StderrFilter(sys.__stderr__)


class WatchdogNode(Node):
    def __init__(self):
        super().__init__('watchdog_system')

        self.containers = {
            'ros2_verrou': {
                'nodes': ['boat_detector', 'usb_cam', 'navigation_verrou'],
                'error_code': 77,
                'restart_done': False,
                'restart_time': None,
                'alert_sent': False,
            },
            'ros2_manuel': {
                'nodes': ['robot_controller', 'bridge_drone'],
                'error_code': 55,
                'restart_done': False,
                'restart_time': None,
                'alert_sent': False,
            },
        }

        self.timeout = 10
        self.ros_domain_id = str(os.environ.get('ROS_DOMAIN_ID', '52'))
        self.current_state = 54
        self.manual_override = None

        self.state_publisher = self.create_publisher(Int32, '/etat_node', 10)
        self.create_subscription(Int32, '/set_etat_mode', self.on_set_etat_mode, 10)
        self.create_timer(2.0, self.check_nodes)
        self.create_timer(5.0, self.publish_state)

        self.get_logger().info(
            f"Watchdog démarré (domain {self.ros_domain_id}) "
            f"— topic: /etat_node | override: /set_etat_mode"
        )

    def on_set_etat_mode(self, msg: Int32):
        value = msg.data
        if value in (54, 55, 77):
            self.manual_override = value
            self.get_logger().info(f"Override manuel activé : état forcé à {value}")
        elif value == 0:
            self.manual_override = None
            self.get_logger().info("Override manuel désactivé — reprise automatique")
        else:
            self.get_logger().warn(
                f"Valeur ignorée : {value}  (valeurs valides : 0, 54, 55, 77)"
            )

    def restart_container(self, container_name: str):
        self.get_logger().warn(f"Restart du container : {container_name}")
        try:
            subprocess.run(
                ['docker', 'restart', container_name],
                check=True,
                timeout=30,
            )
        except Exception as e:
            self.get_logger().error(f"Erreur Docker ({container_name}) : {e}")

    def get_active_nodes_via_cli(self):
        try:
            env = os.environ.copy()
            env['ROS_DOMAIN_ID'] = self.ros_domain_id

            result = subprocess.run(
                ['ros2', 'node', 'list'],
                capture_output=True,
                text=True,
                timeout=3,
                env=env,
            )

            if result.returncode != 0:
                self.get_logger().warn(
                    f"ros2 node list échoué (code {result.returncode}) — cycle ignoré"
                )
                return None

            nodes = set()
            for line in result.stdout.splitlines():
                line = line.strip()
                if line:
                    nodes.add(line.split('/')[-1])
            return nodes

        except subprocess.TimeoutExpired:
            self.get_logger().warn("ros2 node list timeout — cycle ignoré")
            return None
        except Exception as e:
            self.get_logger().warn(f"Erreur ros2 node list : {e} — cycle ignoré")
            return None

    def check_nodes(self):
        active_nodes = self.get_active_nodes_via_cli()
        if active_nodes is None:
            return

        current_time = time.time()
        active_errors = set()

        for container_name, cfg in self.containers.items():
            missing = [n for n in cfg['nodes'] if n not in active_nodes]

            if missing:
                self.get_logger().warn(
                    f"[{container_name}] Nodes manquantes : {missing}"
                )
                if not cfg['restart_done']:
                    self.restart_container(container_name)
                    cfg['restart_done'] = True
                    cfg['restart_time'] = current_time
                    cfg['alert_sent'] = False
                else:
                    elapsed = current_time - cfg['restart_time']
                    if elapsed > self.timeout and not cfg['alert_sent']:
                        self.get_logger().error(
                            f"[{container_name}] Nodes toujours manquantes après restart"
                        )
                        cfg['alert_sent'] = True
                active_errors.add(cfg['error_code'])
            else:
                if cfg['restart_done']:
                    self.get_logger().info(
                        f"[{container_name}] Tous les nodes sont de retour en ligne"
                    )
                cfg['restart_done'] = False
                cfg['restart_time'] = None
                cfg['alert_sent'] = False

        new_state = max(active_errors) if active_errors else 54
        if new_state != self.current_state:
            self.get_logger().info(
                f"Changement d'état : {self.current_state} → {new_state}"
            )
        self.current_state = new_state

    def publish_state(self):
        published_value = (
            self.manual_override
            if self.manual_override is not None
            else self.current_state
        )
        msg = Int32()
        msg.data = published_value
        self.state_publisher.publish(msg)
        self.get_logger().debug(
            f"Publié sur /etat_node : {published_value}"
            + (" (override)" if self.manual_override is not None else "")
        )


def main(args=None):
    rclpy.init(args=args)
    node = WatchdogNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
