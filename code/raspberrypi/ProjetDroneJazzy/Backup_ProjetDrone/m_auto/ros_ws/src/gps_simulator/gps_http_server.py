import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix
from flask import Flask, jsonify
import threading

app = Flask(__name__)
latest_gps = None

class GPSServer(Node):
    def __init__(self):
        super().__init__('gps_http_bridge')
        self.sub = self.create_subscription(NavSatFix, '/gps/fix', self.callback, 10)

    def callback(self, msg):
        global latest_gps
        latest_gps = {
            "lat": msg.latitude,
            "lon": msg.longitude,
            "alt": msg.altitude
        }

def flask_thread():
    app.run(host='0.0.0.0', port=5000)

@app.route('/gps')
def get_gps():
    if latest_gps:
        return jsonify(latest_gps)
    else:
        return jsonify({"lat": 0, "lon": 0, "alt": 0})

def main():
    rclpy.init()
    node = GPSServer()

    # Lancer Flask dans un thread séparé
    t = threading.Thread(target=flask_thread)
    t.start()

    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
