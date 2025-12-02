#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import time
import os

OUTPUT_DIRECTORY = '/tmp/astra_images'

class ImageSaver(Node):
    def __init__(self):
        super().__init__('astra_image_saver')
        self.rgb_subscription = self.create_subscription(
            Image,
            '/astra/color/image_raw',
            self.listener_callback,
            10
        )
        self.bridge = CvBridge()
        self.last_save_time = 0
        self.save_interval = 1.0  # seconds
        self.output_dir = OUTPUT_DIRECTORY

        os.makedirs(self.output_dir, exist_ok=True)
        self.get_logger().info(f"Saving images to: {self.output_dir}")

    def listener_callback(self, msg):
        now = time.time()
        if now - self.last_save_time >= self.save_interval:
            try:
                cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
                filename = os.path.join(self.output_dir, f"image_{int(now)}.jpg")
                cv2.imwrite(filename, cv_image)
                self.get_logger().info(f"Saved {filename}")
                self.last_save_time = now
            except Exception as e:
                self.get_logger().error(f"Failed to save image: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = ImageSaver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()