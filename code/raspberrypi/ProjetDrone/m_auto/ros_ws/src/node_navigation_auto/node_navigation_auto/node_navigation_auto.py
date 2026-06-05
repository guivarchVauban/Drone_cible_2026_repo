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
DEFAULT_LINEAR_SPEED      = 8   # m/s
DEFAULT_MAX_ANGULAR_SPEED = 0.8   # rad/s
DEFAULT_WAYPOINT_RADIUS   = 1.5   # m
DEFAULT_KP_ANGULAR        = 0.4
DEFAULT_KP_LINEAR         = 0.5
# Dans la simulation, le yaw /odometry/filtered est opposé au sens d'avance visuel.
# On réaligne ici le cap utilisé par le contrôleur de navigation.
DEFAULT_YAW_OFFSET        = math.pi
DEFAULT_HEADING_BIAS      = math.radians(-2.0)
DEFAULT_HEADING_DEADBAND  = math.radians(30.0)
DEFAULT_CMD_FILTER_ALPHA  = 1.0
DEFAULT_ANGULAR_DEADBAND  = 0.03
DEFAULT_LINEAR_DEADBAND   = 0.05
DEFAULT_DRIFT_GAIN        = 1.0
DEFAULT_DRIFT_DEADBAND    = 2.0
DEFAULT_WAYPOINT_HOLD_CYCLES = 3

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
        self.declare_parameter('yaw_offset',         DEFAULT_YAW_OFFSET)
        self.declare_parameter('heading_bias',       DEFAULT_HEADING_BIAS)
        self.declare_parameter('heading_deadband',   DEFAULT_HEADING_DEADBAND)
        self.declare_parameter('cmd_filter_alpha',   DEFAULT_CMD_FILTER_ALPHA)
        self.declare_parameter('angular_deadband',   DEFAULT_ANGULAR_DEADBAND)
        self.declare_parameter('linear_deadband',    DEFAULT_LINEAR_DEADBAND)
        self.declare_parameter('drift_correction_gain', DEFAULT_DRIFT_GAIN)
        self.declare_parameter('drift_correction_deadband', DEFAULT_DRIFT_DEADBAND)
        self.declare_parameter('waypoint_hold_cycles', DEFAULT_WAYPOINT_HOLD_CYCLES)
        self.declare_parameter('invert_angular_sign', False)
        self.declare_parameter('autonomous_mode_value', AUTONOMOUS_MODE_VALUE)

        # ------------------------------------------------------------------ #
        # État interne
        # ------------------------------------------------------------------ #
        self.robot_mode: str = ""          # valeur brute reçue sur /robot_mode

        self.current_lat: float | None = None
        self.current_lon: float | None = None

        self.target_lat:  float | None = None
        self.target_lon:  float | None = None
        self.path_anchor_lat: float | None = None
        self.path_anchor_lon: float | None = None

        self.current_yaw:   float = 0.0
        self.current_speed: float = 0.0
        self.gps_vx: float = 0.0
        self.gps_vy: float = 0.0
        self.gps_heading: float | None = None
        self.gps_heading_raw: float | None = None
        self.gps_msg_count: int = 0
        self.last_yaw_time = None
        self.filtered_linear_x: float | None = None
        self.filtered_angular_z: float | None = None
        self.waypoint_reached_cycles = 0

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

        # ------------------------------------------------------------------ #
        # Timer de diagnostic 0.2 Hz (5 secondes)
        # ------------------------------------------------------------------ #
        self.diag_timer = self.create_timer(5.0, self._diagnostic_loop)

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
        new_target = (msg.x, msg.y)
        current_target = (self.target_lat, self.target_lon)
        is_same = self._is_same_waypoint(new_target, current_target)
        
        wp_distance = 0.0
        if current_target[0] is not None and current_target[1] is not None:
            wp_distance = self._haversine(
                current_target[0], current_target[1],
                new_target[0], new_target[1]
            )
        
        self.get_logger().info(
            f'[E5] old={current_target} new={new_target} dist={wp_distance:.2f}m is_same={is_same}'
        )
        
        if is_same:
            return

        self.target_lat, self.target_lon = new_target
        self.waypoint_reached_cycles = 0

        # Réinitialise l’ancre de trajectoire au point de départ du waypoint courant.
        if self.current_lat is not None and self.current_lon is not None:
            self.path_anchor_lat = self.current_lat
            self.path_anchor_lon = self.current_lon
        else:
            self.path_anchor_lat = None
            self.path_anchor_lon = None

        self.get_logger().info(
            f'[E5_ACCEPT] target=({self.target_lat:.8f}, {self.target_lon:.8f})'
        )

    def _cb_odometry_filtered(self, msg: Odometry) -> None:
        """Cap courant (yaw) depuis l'odométrie filtrée."""
        q = msg.pose.pose.orientation
        yaw_offset = self.get_parameter('yaw_offset').value
        yaw_raw = self._quat_to_yaw(q.x, q.y, q.z, q.w)
        self.current_yaw = self._normalize_angle(yaw_raw + yaw_offset)
        self.last_yaw_time = self.get_clock().now()
        
        self.get_logger().info(
            f'[FILTERED_ODOM] yaw_raw={math.degrees(yaw_raw):.1f}° offset={math.degrees(yaw_offset):.1f}° yaw_final={math.degrees(self.current_yaw):.1f}°'
        )

    def _cb_odometry_gps(self, msg: Odometry) -> None:
        """Vitesse courante depuis l'odométrie GPS."""
        vx = msg.twist.twist.linear.x
        vy = msg.twist.twist.linear.y
        self.current_speed = math.hypot(vx, vy)
        self.gps_vx = vx
        self.gps_vy = vy
        self.gps_msg_count += 1
        
        self.get_logger().info(
            f'[GPS_ODOM] msg_count={self.gps_msg_count} vx={vx:.4f} vy={vy:.4f} speed={self.current_speed:.4f}'
        )
        
        if self.current_speed > 0.01:
            # Conserve le cap brut calculé depuis la vitesse pour diagnostics
            self.gps_heading_raw = math.atan2(vy, vx)
            # Par défaut on expose gps_heading = raw (la sélection finale se fera
            # dans la boucle de contrôle où l'on compare avec le yaw filtré).
            self.gps_heading = self.gps_heading_raw
            self.get_logger().info(
                f'[GPS_ODOM] msg_count={self.gps_msg_count} vx={vx:.4f} vy={vy:.4f} '
                f'speed={self.current_speed:.4f} raw_h={math.degrees(self.gps_heading_raw):.1f}°'
            )

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

        # Validation du waypoint : on attend plusieurs cycles consécutifs dans le rayon
        # pour éviter un arrêt prématuré à cause du bruit GPS ou d’un passage transitoire.
        if distance < waypoint_radius:
            self.waypoint_reached_cycles += 1
        else:
            self.waypoint_reached_cycles = 0

        if self.waypoint_reached_cycles >= int(self.get_parameter('waypoint_hold_cycles').value):
            self.get_logger().info(
                f'Waypoint confirmé (distance={distance:.2f} m, cycles={self.waypoint_reached_cycles}). Arrêt.'
            )
            self._publish_stop()
            self.waypoint_reached_cycles = 0
            return

        # Conversion bearing géographique (Nord=0, CW) → angle ENU (Est=0, CCW)
        # formule : angle_ENU = pi/2 - bearing
        bearing_enu = self._normalize_angle(math.pi / 2.0 - bearing)

        # Sélection robuste du cap utilisé pour la navigation.
        # On compare le cap GPS (issu de la vitesse) et le yaw filtré, et on
        # corrige automatiquement les décalages de 90° ou 180° si détectés.
        heading = self._choose_heading(self.gps_heading_raw, self.current_yaw, self.current_speed, self.last_yaw_time)

        # Erreur angulaire dans le référentiel ENU
        heading_bias = self.get_parameter('heading_bias').value
        angle_error = self._normalize_angle(bearing_enu - heading + heading_bias)

        # Log de diagnostic étendu demandé
        self.get_logger().info(
            f'[E3] pos=({self.current_lat:.6f},{self.current_lon:.6f}) '
            f'tgt=({self.target_lat:.6f},{self.target_lon:.6f}) dist={distance:.2f}m '
            f'brg={math.degrees(bearing):.1f}° brg_enu={math.degrees(bearing_enu):.1f}° '
            f'yaw={math.degrees(self.current_yaw):.1f}° gps_raw={math.degrees(self.gps_heading_raw if self.gps_heading_raw else 0):.1f}° '
            f'gps_used={math.degrees(self.gps_heading if self.gps_heading else 0):.1f}° h_used={math.degrees(heading):.1f}° '
            f'err={math.degrees(angle_error):.1f}°'
        )

        # Affichage spécifique des valeurs demandées
        self.get_logger().info(
            f'[DBG_HEADINGS] bearing={math.degrees(bearing):.1f}° bearing_enu={math.degrees(bearing_enu):.1f}° '
            f'gps_heading={math.degrees(self.gps_heading if self.gps_heading is not None else 0):.1f}° '
            f'current_yaw={math.degrees(self.current_yaw):.1f}° angle_error={math.degrees(angle_error):.1f}°'
        )

        # Correction de dérive par écart latéral à la trajectoire.
        drift_correction = 0.0
        drift_cross_track = 0.0
        if None not in (self.path_anchor_lat, self.path_anchor_lon):
            drift_cross_track = self._signed_cross_track_error(
                self.current_lat, self.current_lon,
                self.path_anchor_lat, self.path_anchor_lon,
                self.target_lat, self.target_lon,
            )
            drift_deadband = float(self.get_parameter('drift_correction_deadband').value)
            if abs(drift_cross_track) > drift_deadband:
                drift_correction_gain = float(self.get_parameter('drift_correction_gain').value)
                drift_correction = -drift_correction_gain * math.atan2(
                    drift_cross_track,
                    max(distance, 1.0),
                )
                self.get_logger().info(
                    f'[E4_DRIFT] cross={drift_cross_track:.2f}m corr={math.degrees(drift_correction):.2f}°'
                )

        # Paramètres
        linear_speed      = self.get_parameter('linear_speed').value
        max_angular_speed = self.get_parameter('max_angular_speed').value
        kp_angular        = self.get_parameter('kp_angular').value
        kp_linear         = self.get_parameter('kp_linear').value
        heading_deadband  = float(self.get_parameter('heading_deadband').value)
        cmd_filter_alpha  = float(self.get_parameter('cmd_filter_alpha').value)
        angular_deadband  = float(self.get_parameter('angular_deadband').value)
        linear_deadband   = float(self.get_parameter('linear_deadband').value)

        # Deadband d'alignement : on ignore les très petites erreurs de cap.
        if abs(angle_error) < heading_deadband:
            angle_error = 0.0

        # Commande angulaire proportionnelle, toujours active pendant la trajectoire.
        angular_z = float(
            max(-max_angular_speed,
                min(max_angular_speed, kp_angular * angle_error + drift_correction))
        )

        # Avance tout en s'orientant vers le waypoint.
        # Réduit fermement la vitesse quand l'erreur de cap dépasse 90° afin d'éviter
        # des dérapages et des trajectoires en boucle causés par l'inertie du bateau.
        heading_error_for_speed = min(abs(angle_error), math.pi / 2.0)
        heading_speed_scale = math.cos(heading_error_for_speed)
        heading_speed_scale = max(0.10, heading_speed_scale)
        if abs(angle_error) > math.radians(80.0):
            heading_speed_scale *= 0.5
        
        # PATCH ANTI-BOUCLE: Si distance < 5m ET erreur > 90°, stop la propulsion
        # pour éviter les rotations en boucle dues à l'inertie
        if distance < 5.0 and abs(angle_error) > math.radians(90.0):
            linear_x = 0.0
            self.get_logger().warn(
                f'[E6_SPIRAL] Near WP dist={distance:.2f}m err={math.degrees(angle_error):.1f}° -> STOP linear'
            )
        else:
            linear_x = float(linear_speed * heading_speed_scale)
        phase = 'TRACK'

        # Lissage désactivé par défaut pour éviter le retard de correction.
        if cmd_filter_alpha >= 0.999:
            filtered_linear_x = linear_x
            filtered_angular_z = angular_z
        else:
            if self.filtered_linear_x is None:
                filtered_linear_x = linear_x
            else:
                filtered_linear_x = (
                    cmd_filter_alpha * self.filtered_linear_x
                    + (1.0 - cmd_filter_alpha) * linear_x
                )

            if self.filtered_angular_z is None:
                filtered_angular_z = angular_z
            else:
                filtered_angular_z = (
                    cmd_filter_alpha * self.filtered_angular_z
                    + (1.0 - cmd_filter_alpha) * angular_z
                )

        # Seuils autour de zéro pour éliminer les micro-corrections
        if abs(filtered_linear_x) < linear_deadband:
            filtered_linear_x = 0.0
        if abs(filtered_angular_z) < angular_deadband:
            filtered_angular_z = 0.0

        self.filtered_linear_x = filtered_linear_x
        self.filtered_angular_z = filtered_angular_z

        invert_angular_sign = bool(self.get_parameter('invert_angular_sign').value)
        commanded_angular_z = -filtered_angular_z if invert_angular_sign else filtered_angular_z

        cmd = Twist()
        cmd.linear.x  = filtered_linear_x
        cmd.angular.z = commanded_angular_z
        self.pub_cmd_vel.publish(cmd)

        self.get_logger().info(
            f'phase={phase} dist={distance:.2f}m  '
            f'bearing_geo={math.degrees(bearing):.1f}°  '
            f'bearing_enu={math.degrees(bearing_enu):.1f}°  '
            f'yaw={math.degrees(self.current_yaw):.1f}°  '
            f'err={math.degrees(angle_error):.1f}°  '
            f'cross_track={drift_cross_track:.2f}m  '
            f'drift_corr={math.degrees(drift_correction):.2f}°  '
            f'lin_raw={linear_x:.3f} lin_f={filtered_linear_x:.3f}  '
            f'ang_raw={angular_z:.3f} ang_cmd={commanded_angular_z:.3f}'
        )

    # ---------------------------------------------------------------------- #
    # Diagnostic
    # ---------------------------------------------------------------------- #

    def _diagnostic_loop(self) -> None:
        """Affiche l'état global du système toutes les 5 secondes."""
        self.get_logger().info(
            f'[DIAG] mode={self.robot_mode} gps_count={self.gps_msg_count} '
            f'speed={self.current_speed:.2f}m/s gps_h={math.degrees(self.gps_heading if self.gps_heading else 0):.1f}° '
            f'yaw={math.degrees(self.current_yaw):.1f}° '
            f'target=({self.target_lat}, {self.target_lon})'
        )

    def _choose_heading(self, gps_raw: float | None, current_yaw: float, current_speed: float, last_yaw_time) -> float:
        """Choisit et corrige un cap utilisable pour la navigation.

        Stratégie :
        - Si pas de cap GPS disponible, on retourne `current_yaw`.
        - Sinon on teste quatre candidats (raw, raw±90°, raw+180°) et on choisit
          celui qui est le plus proche du `current_yaw`.
        - Si la meilleure correspondance est trop éloignée, on rejette le GPS
          et on tombe sur `current_yaw` (évite les sauts de 180° / spirales).
        - On met à jour `self.gps_heading` avec le candidat retenu pour cohérence.
        """
        if gps_raw is None:
            return current_yaw

        # Construire candidats et normaliser
        candidates = [gps_raw, gps_raw + math.pi/2.0, gps_raw - math.pi/2.0, gps_raw + math.pi]
        candidates = [self._normalize_angle(c) for c in candidates]

        # Comparer à current_yaw
        diffs = [abs(self._normalize_angle(c - current_yaw)) for c in candidates]
        min_idx = int(min(range(len(diffs)), key=lambda i: diffs[i]))
        best = candidates[min_idx]
        best_diff = diffs[min_idx]

        # seuils (en radians)
        accept_threshold_movable = math.radians(135.0)  # si on bouge, on accepte plus
        accept_threshold_still = math.radians(90.0)

        # Estimation fraîcheur du yaw
        yaw_fresh = False
        if last_yaw_time is not None:
            elapsed = self.get_clock().now() - last_yaw_time
            yaw_fresh = (elapsed.nanoseconds < 1_000_000_000)

        # Règle d'acceptation
        if current_speed > 0.3:
            accept = (best_diff <= accept_threshold_movable)
        else:
            # si on est lent, on favorise le yaw filtré si disponible
            if yaw_fresh:
                accept = (best_diff <= accept_threshold_still)
            else:
                accept = (best_diff <= accept_threshold_movable)

        if accept:
            # Mettre à jour gps_heading avec la correction détectée
            prev = self.gps_heading
            self.gps_heading = self._normalize_angle(best)
            if prev is None:
                prev = float('nan')
            # Détecter et loguer décalages courants
            delta = abs(self._normalize_angle(self.gps_heading_raw - self.gps_heading))
            if delta > math.radians(80) and delta < math.radians(100):
                self.get_logger().warn(f'[HEAD_CORR] detected ~90° offset, corrected gps heading by {math.degrees(delta):.1f}°')
            elif delta > math.radians(170):
                self.get_logger().warn(f'[HEAD_CORR] detected ~180° offset, corrected gps heading by {math.degrees(delta):.1f}°')
            if self.gps_heading != prev:
                self.get_logger().info(f'[HEAD_SEL] using corrected gps heading {math.degrees(self.gps_heading):.1f}° (raw {math.degrees(self.gps_heading_raw):.1f}°)')
            return self.gps_heading
        else:
            # Rejette le cap GPS ; on tombe sur le yaw filtré si récent, sinon sur yaw brut
            self.get_logger().warn(f'[HEAD_REJ] gps heading inconsistent (best_diff={math.degrees(best_diff):.1f}°) -> using yaw')
            return current_yaw

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
    def _is_same_waypoint(
        waypoint_a: tuple[float | None, float | None],
        waypoint_b: tuple[float | None, float | None],
        tolerance: float = 1e-6,
    ) -> bool:
        if None in waypoint_a or None in waypoint_b:
            return False
        return (
            abs(waypoint_a[0] - waypoint_b[0]) < tolerance
            and abs(waypoint_a[1] - waypoint_b[1]) < tolerance
        )

    def _signed_cross_track_error(
        self,
        current_lat: float | None,
        current_lon: float | None,
        anchor_lat: float | None,
        anchor_lon: float | None,
        target_lat: float | None,
        target_lon: float | None,
    ) -> float:
        if None in (current_lat, current_lon, anchor_lat, anchor_lon, target_lat, target_lon):
            return 0.0

        current_x, current_y = self._lat_lon_to_local_xy(current_lat, current_lon, anchor_lat, anchor_lon)
        target_x, target_y = self._lat_lon_to_local_xy(target_lat, target_lon, anchor_lat, anchor_lon)

        line_x = target_x
        line_y = target_y
        line_length = math.hypot(line_x, line_y)
        if line_length < 1e-6:
            return 0.0

        cross_track = (current_y * line_x - current_x * line_y) / line_length
        return cross_track

    @staticmethod
    def _lat_lon_to_local_xy(lat: float, lon: float, ref_lat: float, ref_lon: float) -> tuple[float, float]:
        earth_radius = 6_371_000.0
        lat_rad = math.radians(lat)
        ref_lat_rad = math.radians(ref_lat)
        lon_rad = math.radians(lon)
        ref_lon_rad = math.radians(ref_lon)

        x = (lon_rad - ref_lon_rad) * math.cos(ref_lat_rad) * earth_radius
        y = (lat_rad - ref_lat_rad) * earth_radius
        return x, y

    @staticmethod
    def _quat_to_yaw(x, y, z, w) -> float:
        siny_cosp = 2.0 * (w * z + x * y)
        cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
        return math.atan2(siny_cosp, cosy_cosp)

    def _publish_stop(self) -> None:
        self.filtered_linear_x = None
        self.filtered_angular_z = None
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
