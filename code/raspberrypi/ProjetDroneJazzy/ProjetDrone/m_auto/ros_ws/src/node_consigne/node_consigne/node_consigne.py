import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point

import json
import math
import serial
import pynmea2


class NoeudConsigne(Node):

    def __init__(self):
        super().__init__('node_consigne')

        # Paramètres
        self.declare_parameter("geojson_file", "/root/ros_ws/Waypoints/waypoints.json")
        self.declare_parameter("gps_port", "/dev/ttyUSB1")
        self.declare_parameter("baudrate", 4800)
        self.declare_parameter("tolerance", 5.0)

        geojson_file = self.get_parameter("geojson_file").value
        gps_port = self.get_parameter("gps_port").value
        baudrate = self.get_parameter("baudrate").value
        self.tolerance = self.get_parameter("tolerance").value

        # Chargement waypoints
        self.waypoints = self.load_waypoints(geojson_file)
        self.index_courant = 0

        # GPS
        self.ser = serial.Serial(gps_port, baudrate, timeout=1)

        # Publisher vers navigation
        self.publisher_ = self.create_publisher(Point, "consigne_waypoint", 10)

        # Timer principal
        self.timer = self.create_timer(1.0, self.main_loop)

        self.get_logger().info(f"{len(self.waypoints)} waypoints chargés.")
        self.get_logger().info("Noeud Consigne ROS2 démarré.")

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

    def get_position_gps(self):
        while True:
            line = self.ser.readline().decode('ascii', errors='replace')

            if line.startswith('$GPGGA') or line.startswith('$GNGGA'):
                try:
                    msg = pynmea2.parse(line)
                    if msg.latitude and msg.longitude:
                        return msg.latitude, msg.longitude
                except:
                    continue

    def main_loop(self):

        if self.index_courant >= len(self.waypoints):
            self.get_logger().info("Mission terminée.")
            return

        lat_gps, lon_gps = self.get_position_gps()
        wp = self.waypoints[self.index_courant]

        distance = self.distance_gps(
            lat_gps,
            lon_gps,
            wp["lat"],
            wp["lon"]
        )

        self.get_logger().info(
            f"WP {self.index_courant+1} | Distance: {distance:.2f} m"
        )

        # Publication vers navigation
        msg = Point()
        msg.x = wp["lat"]
        msg.y = wp["lon"]
        msg.z = 0.0
        self.publisher_.publish(msg)

        if distance <= self.tolerance:
            self.get_logger().info("Waypoint atteint !")
            self.index_courant += 1


# === MAIN OBLIGATOIRE POUR ROS2 ===
def main(args=None):
    rclpy.init(args=args)
    node = NoeudConsigne()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
