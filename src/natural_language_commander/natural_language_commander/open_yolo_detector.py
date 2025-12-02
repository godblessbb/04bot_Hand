import rclpy
from rclpy.node import Node
from std_msgs.msg import String, ColorRGBA
from sensor_msgs.msg import Image, CameraInfo
from hand_control_msgs.msg import Object, ObjectList
from visualization_msgs.msg import Marker

import os
import cv2
import cv_bridge
import re
import ast
import numpy as np

from ultralytics import YOLOWorld
import tf2_ros

ADDITIONAL_VOCABULARY = [
    "ball", "brick"
]
DEFAULT_VOCABULARY = [
    "cup", "kettle", "scissors", "fork", "book","bottle","hat",
]

class DetectorNode(Node):
    def __init__(self):
        super().__init__('object_detector')

        self.objects_publisher = self.create_publisher(ObjectList, 'objects_details', 10)
        self.points_publisher = self.create_publisher(Marker, 'objects_points', 10)
        
        self.objects = []
        self.depth_img = None
        self.camera_info = None

        self.bridge = cv_bridge.CvBridge()
        self.camera_tf = None

        # Create a YOLO-World model
        self.model = YOLOWorld("/home/brad/AI_hand/yolov8l-worldv2.pt")  # or select yolov8m/l-world.pt for different sizes
        self.model.to("cuda")
        self.model.set_classes(DEFAULT_VOCABULARY)  # Set the classes to the custom vocabulary
        self.get_logger().info(f"Load YOLO model on device {self.model.device}")

        self.rgb_subscription = self.create_subscription(
            Image,
            '/astra/color/image_raw',
            self.img_callback,
            1)
        self.rgb_subscription  # prevent unused variable warning
        self.depth_subscription = self.create_subscription(
            Image,
            '/astra/depth/image_raw',
            self.depth_callback,
            1)
        self.depth_subscription  # prevent unused variable warning
        self.camera_info_subscription = self.create_subscription(
            CameraInfo,
            '/astra/color/camera_info',
            self.camera_info_callback,
            1)
        self.camera_info_subscription  # prevent unused variable warning
        self.objects_subscription = self.create_subscription(
            String,
            'objects',
            self.objects_callback,
            10)
        self.objects_subscription  # prevent unused variable warning

    def img_callback(self, msg):
        if not self.objects:
            return

        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        # Resize to 640x640 for YOLO
        resized_image = cv2.resize(cv_image, (640, 640))

        results = self.model(resized_image, conf=0.1, verbose=False)

        annotated_frame = results[0].plot()
        # Show the annotated frame in the OpenCV window
        cv2.imshow("YOLOWorld Detection", annotated_frame)
        cv2.waitKey(1)

        if self.depth_img is None or self.camera_info is None:
            self.get_logger().warn("Depth image or camera info not available.")
            return

        cv_depth_image = self.bridge.imgmsg_to_cv2(self.depth_img, desired_encoding='passthrough')
        self._publish_objects(results, cv_depth_image)

    def depth_callback(self, msg):
        self.depth_img = msg

    def camera_info_callback(self, msg):
        self.camera_info = msg

        if self.camera_tf is None:
            self._lookup_camera_tf()

    def objects_callback(self, msg):
        self.objects = None
        try:
            # data = re.sub(r"^```python\n|\n```$", "", msg.data.strip())
            objects = ast.literal_eval(msg.data)
            objects += ADDITIONAL_VOCABULARY
            # Update new vocabulary based on the received objects
            if objects:
                self.model.set_classes(objects)
                self.objects = objects
                self.get_logger().info(f"Updated objects: {self.objects} to detection model.")
        except:
            return
        
    def _lookup_camera_tf(self):
        if not hasattr(self, 'tf_buffer'):
            self.tf_buffer = tf2_ros.Buffer()
            self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        try:
            trans = self.tf_buffer.lookup_transform(
                'world',  # target frame
                self.camera_info.header.frame_id,  # source frame
                rclpy.time.Time())
            self.camera_tf = trans
            self.get_logger().info(f"Camera transform found: {trans}")
        except Exception as e:
            self.get_logger().warn(f"Could not lookup camera transform: {e}")

    def _publish_objects(self, results, depth_image):
        # Extract bounding boxes, classes, names, and confidences
        boxes = results[0].boxes.xywh.tolist()
        classes = results[0].boxes.cls.tolist()
        names = results[0].names
        confidences = results[0].boxes.conf.tolist()

        object_list = ObjectList()

        # Iterate through the results
        for box, cls, conf in zip(boxes, classes, confidences):
            obj = Object()
            x, y, w, h = box
            # Rescale xywh from 640x640 to depth image size
            depth_h, depth_w = depth_image.shape[:2]
            # scale_x = depth_w / 640
            scale_y = depth_h / 640
            # x *= scale_x
            # w *= scale_x
            y *= scale_y
            h *= scale_y
            obj.name = self.objects[int(cls)]
            for px in [x - w/6, x, x + w/6]:
                for py in [y - h/6, y, y + h/6]:
                    if 0 <= px < depth_image.shape[1] and 0 <= py < depth_image.shape[0]:
                        point = self._cvt_depth_to_xyz(depth_image, int(px), int(py))
                        w_point = self.transform_point(point)
                        obj.points.append(w_point)
            object_list.objects.append(obj)
            
        self.objects_publisher.publish(object_list)
        marker = self._create_marker(object_list)
        self.points_publisher.publish(marker)

    def _create_marker(self, object_list):
        marker = Marker()
        marker.header.frame_id = "world"
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "detected_objects"
        marker.id = 0
        marker.type = Marker.POINTS
        marker.action = Marker.ADD
        marker.scale.x = 0.05
        marker.scale.y = 0.05
        marker.scale.z = 0.05
        marker.color.a = 1.0
        marker.color.r = 1.0
        marker.color.g = 0.0
        marker.color.b = 0.0

        for obj in object_list.objects:
            # Assign a unique color for each object using a color map
            color_map = [
                (1.0, 0.0, 0.0),  # Red
                (0.0, 1.0, 0.0),  # Green
                (0.0, 0.0, 1.0),  # Blue
                (1.0, 1.0, 0.0),  # Yellow
                (1.0, 0.0, 1.0),  # Magenta
                (0.0, 1.0, 1.0),  # Cyan
                (1.0, 0.5, 0.0),  # Orange
                (0.5, 0.0, 1.0),  # Purple
            ]
            obj_idx = object_list.objects.index(obj) % len(color_map)
            r, g, b = color_map[obj_idx]
            for point in obj.points:
                marker.points.append(point)
                marker.colors.append(ColorRGBA(r=r, g=g, b=b, a=1.0))

        return marker

    def _cvt_depth_to_xyz(self, depth, px, py):
        # Convert depth image to 3D point cloud
         # Intrinsics
        fx = self.camera_info.k[0]
        fy = self.camera_info.k[4]
        cx = self.camera_info.k[2]
        cy = self.camera_info.k[5]

        half = 15 // 2

        # Clip window to image bounds
        y_min = max(py - half, 0)
        y_max = min(py + half + 1, depth.shape[0])
        x_min = max(px - half, 0)
        x_max = min(px + half + 1, depth.shape[1])

        # Extract window and apply median
        window = depth[y_min:y_max, x_min:x_max].astype(np.float32)
        
        z = np.median(window) / 1000.0  # convert mm → m

        # Back-project to 3D (camera frame)
        x = (px - cx) * z / fx
        y = (py - cy) * z / fy

        return np.array([x, y, z])
    
    def transform_point(self, point):
        if self.camera_tf is None:
            self.get_logger().warn("Camera transform not available.")
            return point

        # Transform the point to the world frame
        import geometry_msgs.msg
        from tf2_geometry_msgs import do_transform_point

        point_msg = geometry_msgs.msg.PointStamped()
        point_msg.header.frame_id = self.camera_info.header.frame_id
        point_msg.point.x, point_msg.point.y, point_msg.point.z = point[0], point[1], point[2]

        transformed_point = do_transform_point(point_msg, self.camera_tf)
        return transformed_point.point

def main(args=None):
    rclpy.init(args=args)
    node = DetectorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()