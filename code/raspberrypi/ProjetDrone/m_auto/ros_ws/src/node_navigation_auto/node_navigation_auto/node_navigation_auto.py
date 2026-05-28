#!/usr/bin/env python3
"""
node_navigation_auto.py
-----------------------
Noeud ROS2 de navigation autonome pour le drone cible.

Souscriptions :
  /fix                      (sensor_msgs/NavSatFix)   – position GPS courante (simulateur)
  /consigne_waypoint        (geometry_msgs/Point)     – waypoint cible (x=lat, y=lon)
  /odometry/filtered        (nav_msgs/Odometry)       – odométrie filtrée → yaw
  /odometry/gps             (nav_msgs/Odometry)       – odométrie GPS → vitesse
  /robot_mode               (std_msgs/String)         – mode actif ("1" = autonome)

Publication :
  /cmd_vel                  (geometry_msgs/Twist)     – commande de vitesse
"""

import math
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

from std_msgs.msg import String
from sensor_msgs.msg import NavSatFix
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist, Point


# ---------------------------------------------------------------------------
# Paramètres de navigation
# ---------------------------------------------------------------------------
DEFAULT_LINEAR_SPEED      = 0.3   # m/s
DEFAULT_MAX_ANGULAR_SPEED = 0.8   # rad/s
DEFAULT_WAYPOINT_RADIUS   = 1.5   # m
DEFAULT_KP_ANGULAR        = 1.2
DEFAULT_KP_LINEAR         = 0.5

# Valeur du topic /robot_mode qui active le mode autonome
AUTONOMOUS_MODE_VALUE = "1"


class NodeNavigationAuto(Node):
    """Nœud de navigation autonome GPS + odométrie."""

    def __init__(self):
        super().__init__('node_navigation_auto')

        # ------------------------------------------------------------------ #
        # Paramètres ROS2
        # ------------------------------------------------------------------ #
        self.declare_parameter('linear_speed',       DEFAULT_LINEAR_SPEED)
        self.declare_parameter('max_angular_speed',  DEFAULT_MAX_ANGULAR_SPEED)
        self.declare_parameter('waypoint_radius',    DEFAULT_WAYPOINT_RADIUS)
        self.declare_parameter('kp_angular',         DEFAULT_KP_ANGULAR)
        self.declare_parameter('kp_linear',          DEFAULT_KP_LINEAR)
        self.declare_parameter('autonomous_mode_value', AUTONOMOUS_MODE_VALUE)

        # ------------------------------------------------------------------ #
        # État interne
        # ------------------------------------------------------------------ #
        self.robot_mode: str = ""          # valeur brute reçue sur /robot_mode

        self.current_lat: float | None = None
        self.current_lon: float | None = None

        self.target_lat:  float | None = None
        self.target_lon:  float | None = None

        self.current_yaw:   float = 0.0
        self.current_speed: float = 0.0

        # ------------------------------------------------------------------ #
        # QoS capteurs
        # ------------------------------------------------------------------ #
        # BEST_EFFORT pour odometry
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            depth=10,
        )
        # RELIABLE pour GPS (la plupart des drivers NavSat publient en RELIABLE)
        gps_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            depth=10,
        )

        # ------------------------------------------------------------------ #
        # Souscriptions
        # ------------------------------------------------------------------ #

        # /robot_mode → std_msgs/String
        self.create_subscription(
            String,
            '/robot_mode',
            self._cb_robot_mode,
            10,
        )

        # /fix → sensor_msgs/NavSatFix (position GPS courante du simulateur)
        self.create_subscription(
            NavSatFix,
            '/fix',
            self._cb_nav_sat_fix,
            gps_qos,
        )

        # /consigne_waypoint → geometry_msgs/Point  (x=lat, y=lon)
        self.create_subscription(
            Point,
            '/consigne_waypoint',
            self._cb_consigne_waypoint,
            10,
        )

        # /odometry/filtered → nav_msgs/Odometry (yaw)
        self.create_subscription(
            Odometry,
            '/odometry/filtered',
            self._cb_odometry_filtered,
            sensor_qos,
        )

        # /odometry/gps → nav_msgs/Odometry (vitesse)
        self.create_subscription(
            Odometry,
            '/odometry/gps',
            self._cb_odometry_gps,
            sensor_qos,
        )

        # ------------------------------------------------------------------ #
        # Publisher /cmd_vel
        # ------------------------------------------------------------------ #
        self.pub_cmd_vel = self.create_publisher(Twist, '/cmd_vel', 10)

        # ------------------------------------------------------------------ #
        # Timer de contrôle 10 Hz
        # ------------------------------------------------------------------ #
        self.control_timer = self.create_timer(0.1, self._control_loop)

        self.get_logger().info(
            f'node_navigation_auto démarré — écoute /fix pour la position GPS. '
            f'Mode autonome activé par robot_mode = "{AUTONOMOUS_MODE_VALUE}"'
        )

    # ---------------------------------------------------------------------- #
    # Callbacks
    # ---------------------------------------------------------------------- #

    def _cb_robot_mode(self, msg: String) -> None:
        """Reçoit le mode robot depuis /robot_mode (std_msgs/String)."""
        previous = self.robot_mode
        self.robot_mode = msg.data.strip()
        if previous != self.robot_mode:
            auto_val = self.get_parameter('autonomous_mode_value').value
            is_auto  = (self.robot_mode == auto_val)
            mode_str = f'AUTONOME (valeur="{self.robot_mode}")' if is_auto \
                       else f'MANUEL (valeur="{self.robot_mode}")'
            self.get_logger().info(f'Mode changé → {mode_str}')
            if not is_auto:
                self._publish_stop()

    def _cb_nav_sat_fix(self, msg: NavSatFix) -> None:
        """Position GPS courante depuis /fix."""
        if msg.status.status < 0:
            return
        self.current_lat = msg.latitude
        self.current_lon = msg.longitude

    def _cb_consigne_waypoint(self, msg: Point) -> None:
        """
        Waypoint cible depuis /consigne_waypoint (geometry_msgs/Point).
        Convention : x = latitude, y = longitude
        """
        self.target_lat = msg.x
        self.target_lon = msg.y
        self.get_logger().info(
            f'Nouveau waypoint reçu : lat={self.target_lat:.6f}, lon={self.target_lon:.6f}'
        )

    def _cb_odometry_filtered(self, msg: Odometry) -> None:
        """Cap courant (yaw) depuis l'odométrie filtrée."""
        q = msg.pose.pose.orientation
        self.current_yaw = self._quat_to_yaw(q.x, q.y, q.z, q.w)

    def _cb_odometry_gps(self, msg: Odometry) -> None:
        """Vitesse courante depuis l'odométrie GPS."""
        vx = msg.twist.twist.linear.x
        vy = msg.twist.twist.linear.y
        self.current_speed = math.hypot(vx, vy)

    # ---------------------------------------------------------------------- #
    # Boucle de contrôle
    # ---------------------------------------------------------------------- #

    def _control_loop(self) -> None:
        auto_val = self.get_parameter('autonomous_mode_value').value

        # Garde mode autonome
        if self.robot_mode != auto_val:
            return

        # Garde données disponibles
        if None in (self.current_lat, self.current_lon,
                    self.target_lat,  self.target_lon):
            self.get_logger().warn(
                'Navigation autonome : en attente de position GPS et/ou waypoint.',
                throttle_duration_sec=5.0,
            )
            return

        # Calcul distance et cap
        distance = self._haversine(
            self.current_lat, self.current_lon,
            self.target_lat,  self.target_lon,
        )
        bearing = self._bearing(
            self.current_lat, self.current_lon,
            self.target_lat,  self.target_lon,
        )

        waypoint_radius = self.get_parameter('waypoint_radius').value

        # Waypoint atteint
        if distance < waypoint_radius:
            self.get_logger().info(
                f'Waypoint atteint (distance={distance:.2f} m). Arrêt.'
            )
            self._publish_stop()
            return

        # Conversion bearing géographique (Nord=0, CW) → angle ENU (Est=0, CCW)
        # formule : angle_ENU = pi/2 - bearing
        bearing_enu = self._normalize_angle(math.pi / 2.0 - bearing)

        # Erreur angulaire dans le référentiel ENU
        angle_error = self._normalize_angle(bearing_enu - self.current_yaw)

        # Paramètres
        linear_speed      = self.get_parameter('linear_speed').value
        max_angular_speed = self.get_parameter('max_angular_speed').value
        kp_angular        = self.get_parameter('kp_angular').value
        kp_linear         = self.get_parameter('kp_linear').value

        # Commandes
        angular_z = float(
            max(-max_angular_speed,
                min(max_angular_speed, kp_angular * angle_error))
        )
        angle_factor    = max(0.0, 1.0 - abs(angle_error) / math.pi)
        distance_factor = min(1.0, kp_linear * distance)
        linear_x        = float(linear_speed * angle_factor * distance_factor)

        cmd = Twist()
        cmd.linear.x  = linear_x
        cmd.angular.z = angular_z
        self.pub_cmd_vel.publish(cmd)

        self.get_logger().info(
            f'dist={distance:.2f}m  '
            f'bearing_geo={math.degrees(bearing):.1f}°  '
            f'bearing_enu={math.degrees(bearing_enu):.1f}°  '
            f'yaw={math.degrees(self.current_yaw):.1f}°  '
            f'err={math.degrees(angle_error):.1f}°  '
            f'lin={linear_x:.3f}  ang={angular_z:.3f}'
        )

    # ---------------------------------------------------------------------- #
    # Utilitaires géographiques
    # ---------------------------------------------------------------------- #

    @staticmethod
    def _haversine(lat1, lon1, lat2, lon2) -> float:
        R = 6_371_000.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)
        a = (math.sin(dphi / 2) ** 2
             + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @staticmethod
    def _bearing(lat1, lon1, lat2, lon2) -> float:
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dlam = math.radians(lon2 - lon1)
        x = math.sin(dlam) * math.cos(phi2)
        y = (math.cos(phi1) * math.sin(phi2)
             - math.sin(phi1) * math.cos(phi2) * math.cos(dlam))
        return math.atan2(x, y)

    @staticmethod
    def _normalize_angle(angle: float) -> float:
        while angle >  math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle

    @staticmethod
    def _quat_to_yaw(x, y, z, w) -> float:
        siny_cosp = 2.0 * (w * z + x * y)
        cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
        return math.atan2(siny_cosp, cosy_cosp)

    def _publish_stop(self) -> None:
        self.pub_cmd_vel.publish(Twist())


# --------------------------------------------------------------------------- #
# Point d'entrée
# --------------------------------------------------------------------------- #

def main(args=None):
    rclpy.init(args=args)
    node = NodeNavigationAuto()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node._publish_stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
