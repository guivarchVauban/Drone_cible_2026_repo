import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from sensor_msgs.msg import NavSatFix

import json
import math


class NoeudConsigne(Node):

    def __init__(self):
        super().__init__('node_consigne')

        # Paramètres
        self.declare_parameter("geojson_file", "/root/ros_ws/Waypoints/waypoints_simu.json")
        self.declare_parameter("tolerance", 7.0)  # entre 5 et 10m

        geojson_file = self.get_parameter("geojson_file").value
        self.tolerance = self.get_parameter("tolerance").value

        # Chargement waypoints
        self.waypoints = self.load_waypoints(geojson_file)
        self.index_courant = 0

        # Position GPS actuelle
        self.current_lat = None
        self.current_lon = None

        # Subscriber GPS (/fix)
        self.subscription = self.create_subscription(
            NavSatFix,
            "/fix",
            self.gps_callback,
            10
        )

        # Publisher waypoint
        self.publisher_ = self.create_publisher(Point, "/consigne_waypoint", 10)

        # Timer
        self.timer = self.create_timer(1.0, self.main_loop)

        self.get_logger().info(f"{len(self.waypoints)} waypoints chargés.")
        self.get_logger().info("Node Consigne ROS2 démarré.")

    def load_waypoints(self, file):
        with open(file, 'r') as f:
            data = json.load(f)

        waypoints = []

        for feature in data["features"]:
            if feature["geometry"]["type"] == "Point":
                lon, lat = feature["geometry"]["coordinates"]
                order = feature["properties"].get("order", 0)

                waypoints.append({
                    "order": order,
                    "lat": lat,
                    "lon": lon
                })

        waypoints.sort(key=lambda x: x["order"])
        return waypoints

    def gps_callback(self, msg):
        self.current_lat = msg.latitude
        self.current_lon = msg.longitude

    def distance_gps(self, lat1, lon1, lat2, lon2):
        R = 6371000

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)

        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi/2)**2 + \
            math.cos(phi1)*math.cos(phi2)*math.sin(delta_lambda/2)**2

        c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R*c

    def publish_waypoint(self):
        wp = self.waypoints[self.index_courant]

        msg = Point()
        msg.x = wp["lat"]
        msg.y = wp["lon"]
        msg.z = 0.0

        self.publisher_.publish(msg)

        self.get_logger().info(
            f"Publication WP {self.index_courant+1} → lat: {wp['lat']} lon: {wp['lon']}"
        )

    def main_loop(self):

        # Pas encore de GPS reçu
        if self.current_lat is None:
            self.get_logger().warn("Pas de GPS reçu (/fix)")
            return

        # Mission terminée
        if self.index_courant >= len(self.waypoints):
            self.get_logger().info("Mission terminée.")
            return

        wp = self.waypoints[self.index_courant]

        distance = self.distance_gps(
            self.current_lat,
            self.current_lon,
            wp["lat"],
            wp["lon"]
        )

        self.get_logger().info(
            f"WP {self.index_courant+1} | Distance: {distance:.2f} m"
        )

        # Si waypoint atteint → passer au suivant
        if distance <= self.tolerance:
            self.get_logger().info("Waypoint atteint ! Passage au suivant.")
            self.index_courant += 1

            if self.index_courant < len(self.waypoints):
                self.publish_waypoint()

        else:
            # Publie uniquement le waypoint courant
            self.publish_waypoint()


# === MAIN ROS2 ===
def main(args=None):
    rclpy.init(args=args)
    node = NoeudConsigne()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
