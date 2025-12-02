#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import threading

from hand_controller.models.robot_state import *
from hand_controller.models.RobotPolicyNet import RobotPolicy
from copy import deepcopy

from sensor_msgs.msg import JointState
from tf2_ros import Buffer, TransformListener
from geometry_msgs.msg import TransformStamped
import os
import json
from hand_control_msgs.msg import ObjectList, HandCommand, JointCommand
from aubo_msgs.srv import SetPoseStampedGoal
import tf_transformations
import time
from geometry_msgs.msg import PoseStamped
from builtin_interfaces.msg import Time
        

class PolicyNode(Node):
    def __init__(self):
        super().__init__('robot_data_collector')

        # Current state
        self.robot_data = RobotData()

        # ROS2 callbacks
        self.hand_joint_states_subscription = self.create_subscription(
            JointState,
            'hand_joint_states',
            self._hand_joint_states_callback,
            10
        )

        self.arm_joint_states_subscription = self.create_subscription(
            JointState,
            'joint_states',
            self._arm_joint_states_callback,
            10
        )

        self.objects_subscription = self.create_subscription(
            ObjectList,
            'objects_details',
            self._objects_callback,
            10
        )

        self.objects = None

        # Continuously lookup transform from the world to the end-effector
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        # Timer to query every 0.1s
        self.timer = self.create_timer(0.1, self._lookup_end_effector_transform)

        """
        Controller policy
        """
        self.declare_parameter("model_path", "")
        model_path = self.get_parameter("model_path").get_parameter_value().string_value
        self.get_logger().info(f"Load policy from: {model_path}")
        self.policy = RobotPolicy()
        self.policy.load_state_dict(torch.load(model_path))

        self.action_started = False

        """
        ROS2 controller API
        """
        self.end_effector_goal_client = self.create_client(
            SetPoseStampedGoal,
            'set_end_effector_pose',
        )

        self.hand_command_publisher = self.create_publisher(
            HandCommand, 
            'hand_command', 
            10
        )

        # Start a background thread for data collection process (example)
        self.data_thread = threading.Thread(target=self.control_loop, daemon=True)
        self.data_thread.start()


    def _hand_joint_states_callback(self, msg: JointState):
        self.robot_data.finger_positions = [msg.position[i] for i in range(len(msg.position))]

    def _arm_joint_states_callback(self, msg: JointState):
        self.robot_data.joint_positions = [msg.position[i] for i in range(len(msg.position))]

    def _lookup_end_effector_transform(self):
        try:
            transform: TransformStamped = self.tf_buffer.lookup_transform(
                "world", "ee_link", rclpy.time.Time()
            )
            
            # Extract quaternion from the transform
            q = transform.transform.rotation
            quaternion = [q.x, q.y, q.z, q.w]

            # Convert quaternion to roll, pitch, yaw
            roll, pitch, yaw = tf_transformations.euler_from_quaternion(quaternion)

            self.robot_data.eef_position = [
                transform.transform.translation.x,
                transform.transform.translation.y,
                transform.transform.translation.z,
                roll, pitch, yaw
            ]

        except Exception as e:
            # In case TF is not available yet
            self.get_logger().warn(f"Could not transform: {e}")

    def _objects_callback(self, msg: ObjectList):
        self.objects = msg.objects

    def control_loop(self):
        while rclpy.ok():
            time.sleep(0.1)
            # Implement your control logic here
            if self.objects is None:
                continue

            ### Temporary for test: action pick the cup
            self.robot_data.action = "pick"
            objects = 'bottle'
            if objects:
                object_names = [name.strip() for name in objects.split(',') if name.strip()]
                self.robot_data.objects.clear()
                for name in object_names:
                    for obj in self.objects:
                        if obj.name == name:
                            point_list = []
                            for point in obj.points:
                                point_list.append([point.x, point.y, point.z])
                            self.robot_data.add_object(obj.name, point_list)
            # self.get_logger().info(f"Robot data: {self.robot_data}")
            # self.get_logger().info(f"Objects: {self.objects}")
            if self.robot_data.objects:
                self.action_started = True

            if not self.action_started:
                continue

            # self.get_logger().info(f"Action: {self.robot_data.action}, Objects: {[obj.name for obj in self.robot_data.objects]}")

            model_input = self.robot_data.to_model_input()
            output = self.policy.forward([model_input]).detach().cpu().numpy().flatten()
            # self.get_logger().info(f"output: {output}")     

            eef_position = output[:3] + self.robot_data.objects[0].position[4]
            eef_orientation = output[3:9]
            finger_positions = output[9:] / DEG_TO_RAD
            eef_rpy = decode_angles(np.array(eef_orientation))
            eef_orientation = eef_rpy.tolist()
            self.get_logger().info(f"Finger positions: {finger_positions}")
            self._publish_finger_command(finger_positions)
            self.get_logger().info(f"Robot eff: {eef_position}, {eef_orientation}")
            self._call_arm_goal(eef_position, eef_orientation)
            self.action_started = False

    def _call_arm_goal(self, eef_position, eef_orientation):
        pose = PoseStamped()
        pose.header.frame_id = "world"
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = float(eef_position[0])
        pose.pose.position.y = float(eef_position[1])
        pose.pose.position.z = float(eef_position[2])

        qx, qy, qz, qw = tf_transformations.quaternion_from_euler(*eef_orientation)
        pose.pose.orientation.x = float(qx)
        pose.pose.orientation.y = float(qy)
        pose.pose.orientation.z = float(qz)
        pose.pose.orientation.w = float(qw)

        # Call the service
        req = SetPoseStampedGoal.Request()
        req.goal = pose
        req.speed_factor = 0.1

        while not self.end_effector_goal_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for end effector goal service...')

        done_event = threading.Event()

        def _arm_goal_response(future):
            try:
                result = future.result()
                if result is not None:
                    self.get_logger().info("End effector goal sent successfully.")
                else:
                    self.get_logger().error("Failed to send end effector goal.")
            except Exception as e:
                self.get_logger().error(f"Service call failed: {e}")
            done_event.set()
        
        future = self.end_effector_goal_client.call_async(req)
        future.add_done_callback(_arm_goal_response)

        done_event.wait()

    def _publish_finger_command(self, finger_positions):
        msg = HandCommand()
        msg.mode = HandCommand.POSITION
        msg.joint_commands = [
            JointCommand(joint='index_pip', value=float(finger_positions[0])),
            JointCommand(joint='index_mcp', value=float(finger_positions[1])),
            JointCommand(joint='index_abd', value=float(finger_positions[2])),
            JointCommand(joint='middle_abd', value=float(finger_positions[3])),
            JointCommand(joint='middle_pip', value=float(finger_positions[4])),
            JointCommand(joint='pinky_mcp', value=float(finger_positions[5])),
            JointCommand(joint='pinky_pip', value=float(finger_positions[6])),
            JointCommand(joint='pinky_abd', value=float(finger_positions[7])),
            JointCommand(joint='middle_mcp', value=float(finger_positions[8])),
            JointCommand(joint='ring_pip', value=float(finger_positions[9])),
            JointCommand(joint='ring_mcp', value=float(finger_positions[10])),
            JointCommand(joint='ring_abd', value=float(finger_positions[11])),
            JointCommand(joint='thumb_pip', value=float(finger_positions[12])),
            JointCommand(joint='thumb_dip', value=float(finger_positions[13])),
            JointCommand(joint='thumb_abd', value=float(finger_positions[14])),
            JointCommand(joint='thumb_mcp', value=float(finger_positions[15])),
        ]

        self.hand_command_publisher.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = PolicyNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()