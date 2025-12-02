#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import threading
import re
import time
from hand_controller.models.robot_state import *
from copy import deepcopy

from sensor_msgs.msg import JointState
from tf2_ros import Buffer, TransformListener
from geometry_msgs.msg import TransformStamped
import os
import json
from hand_control_msgs.msg import ObjectList, Object, HandCommand, JointCommand
# from aubo_msgs.srv import SetPoseStampedGoal
from jaka_msgs.srv import SetPoseStampedGoal
from std_msgs.msg import String
import tf_transformations
from hand_controller.skills.control_interfaces import call_arm_goal, publish_finger_command
from hand_controller.skills.pick_bottle import PickBottle
from hand_controller.skills.place_bottle import PlaceBottle
from hand_controller.skills.pour_water import PourWater
from hand_controller.skills.pick_ball import PickBall
from hand_controller.skills.pick_cube import PickCube
from hand_controller.skills.place_cube_ball import PlaceCubeBall
from hand_controller.skills.drop import Drop


class SkillsOperator(Node):        
    def __init__(self):
        super().__init__('skills_operator')
        # Data collection
        self.data_collection = []
        # Load existing data if file exists
        data_file = '/home/brad/AI_hand/robot_data.json'
        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                try:
                    loaded_data = json.load(f)
                    self.data_collection.extend(RobotData.from_dict(item) for item in loaded_data)
                        
                    self.get_logger().info(f"Loaded {len(self.data_collection)} data entries from {data_file}")
                except Exception as e:
                    self.get_logger().warn(f"Failed to load data from {data_file}: {e}")

        # Current state
        self.robot_data = RobotData()
        
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

        # ROS2 callbacks
        self.voice_command_subscription = self.create_subscription(
            String,
            'voice_commands',
            self._voice_command_callback,
            10
        )
        
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
        self.skills = {
            'pick_bottle': PickBottle(self, self.end_effector_goal_client, self.hand_command_publisher),
            'pour_water': PourWater(self, self.end_effector_goal_client, self.hand_command_publisher),
            'place_bottle': PlaceBottle(self, self.end_effector_goal_client, self.hand_command_publisher),
            'pick_ball': PickBall(self, self.end_effector_goal_client, self.hand_command_publisher),
            'pick_cube': PickCube(self, self.end_effector_goal_client, self.hand_command_publisher),
            'place_cube_ball': PlaceCubeBall(self, self.end_effector_goal_client, self.hand_command_publisher),
            'drop': Drop(self, self.end_effector_goal_client, self.hand_command_publisher),
        }

        self.last_pick_point = None

        # Continuously lookup transform from the world to the end-effector
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        # Timer to query every 0.1s
        self.timer = self.create_timer(0.1, self._lookup_end_effector_transform)

        # Start a background thread for data collection process (example)
        self.data_thread = threading.Thread(target=self.data_collection_loop, daemon=True)
        self.data_thread.start()

        self.command_thread = threading.Thread(target=self.command_loop, daemon=True)
        self.command_thread.start()
        self.new_command = None


    def _hand_joint_states_callback(self, msg: JointState):
        self.robot_data.finger_positions = [msg.position[i] for i in range(len(msg.position))]

    def _arm_joint_states_callback(self, msg: JointState):
        self.robot_data.joint_positions = [msg.position[i] for i in range(len(msg.position))]

    def _lookup_end_effector_transform(self):
        try:
            ee_link = "ee_link" # aubo
            transform: TransformStamped = self.tf_buffer.lookup_transform(
                "world", ee_link, rclpy.time.Time()
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
            # self.get_logger().info(f"EEF position: {self.robot_data.eef_position}", throttle_duration_sec=1)

        except Exception as e:
            # In case TF is not available yet
            self.get_logger().warn(f"Could not transform: {e}")

    def _objects_callback(self, msg: ObjectList):
        # self.get_logger().info(f'New objects: {[obj.name for obj in msg.objects]}')
        self.objects = msg.objects

    def save_data(self, filename='robot_data.json'):
        self.get_logger().info(f'Save: {self.data_collection}')
        with open(filename, 'w') as f:
            json.dump([data.to_dict() for data in self.data_collection], f, indent=4)

    def _voice_command_callback(self, msg: String):
        self.get_logger().info(f"Voice command received: {msg.data}")
        try:
            json_list = json.loads(msg.data)
            if isinstance(json_list, str):
                json_list = json.loads(json_list)
            if isinstance(json_list, dict):
                json_list = [json_list]
            self.get_logger().info(f"Parsed JSON list: {json_list}")
        except Exception as e:
            self.get_logger().warn(f"Failed to parse voice command JSON: {e}")
            return

        self.new_command = json_list

    def command_loop(self):
        while rclpy.ok():
            time.sleep(0.1)
            if self.new_command is None:
                continue

            for item in self.new_command:
                print(f'item: {item}', flush=True)
                if 'action' in item:
                    self.robot_data.action = item['action']
                if 'target_name' in item:
                    self.robot_data.objects.clear()
                    print(f'target: {item['target_name']}', flush=True)
                    for obj in self.objects:
                        print(f'obj name: {obj.name}', flush=True)
                        if obj.name == item['target_name']:
                            point_list = []
                            for point in obj.points:
                                point_list.append([point.x, point.y, point.z])
                            self.robot_data.add_object(obj.name, point_list)
                if not self.robot_data.objects:
                    self.get_logger().warn("No valid objects found in the voice command.")
                    continue
                
                self.perform_skill()

            self.new_command = None

        
            
    
    def data_collection_loop(self):
        while rclpy.ok():
            # Get an intput string
            action_str = input("Enter command (or 'q' to quit, leaving empty to remain the action): ")
            if action_str == 'q':
                break
            if action_str:
                # Update the action in the robot data
                self.robot_data.action = action_str

            # Clear the terminal screen
            os.system('clear' if os.name == 'posix' else 'cls')
            objects = input("Enter object names (comma-separated, leaving empty to remain the objects): ")
            if self.objects is None:
                self.get_logger().warn("No objects detected yet, please wait for detection.")
                continue
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

            if not self.robot_data.objects:
                self.get_logger().warn("No objects found.")
                continue

            self.perform_skill()
        self.save_data()
        

    def perform_skill(self):
        if self.robot_data.action in ['pick', 'grasp', 'grab', 'take'] and self.contains_substring(self.robot_data.objects[0].name, ['bottle', 'cup']):
            skill = 'pick_bottle'
        elif self.robot_data.action in ['pour', 'tilt'] and self.contains_substring(self.robot_data.objects[0].name, ['cup']):
            skill = 'pour_water'
        elif self.robot_data.action in ['place', 'put', 'drop'] and self.contains_substring(self.robot_data.objects[0].name, ['bottle', 'cup']):
            skill = 'place_bottle'
        elif self.robot_data.action in ['pick', 'grasp', 'grab', 'take'] and self.contains_substring(self.robot_data.objects[0].name, ['ball']):
            skill = 'pick_ball'
        elif self.robot_data.action in ['pick', 'grasp', 'grab', 'take'] and self.contains_substring(self.robot_data.objects[0].name, ['cube', 'box', 'toy', 'brick']):
            skill = 'pick_cube'
        # elif self.robot_data.action in ['place', 'put'] and self.contains_substring(self.robot_data.objects[0].name, ['cube', 'box', 'ball', 'toy']):
        #     skill = 'place_cube_ball'
        elif self.robot_data.action in ['drop', 'release', 'place', 'pour'] and len(self.robot_data.objects) >= 1:
            skill = 'drop'
        else:
            self.get_logger().warn(f"Unknown action or object: {self.robot_data.action} with {self.robot_data.objects[0].name}")
            return

        target_point = self.robot_data.objects[0].position[4]
        for point_idx in [4, 3, 5, 1, 0, 2, 7, 6, 8]:
            if self.robot_data.objects[0].position[point_idx][0] > -0.6:    # invalid
                target_point = self.robot_data.objects[0].position[point_idx]
                break
        if self.robot_data.action in ['pick', 'grasp', 'grab', 'take']:
            self.last_pick_point = target_point
        elif self.robot_data.action in ['place', 'put'] and not self.contains_substring(self.robot_data.objects[0].name, ['basket', 'box']):
            target_point = self.last_pick_point

        for step in self.skills[skill].STEPS_ORDER.keys():
            self.get_logger().info(f"Perform skill {skill} at step: {step}")
            
            self.skills[skill].execute(step, target_point)

            self.get_logger().info(f"Collected data: {self.robot_data}")

            # Append the current state to the data collection
            self.data_collection.append(deepcopy(self.robot_data))
            
    
    @staticmethod
    def contains_substring(text, substrings):
        """
        Check if the text contains any of the substrings from the list.

        Args:
            text (str): The text to search in.
            substrings (list of str): List of substrings to check.

        Returns:
            bool: True if any substring is found, False otherwise.
        """
        pattern = "|".join(map(re.escape, substrings))
        return bool(re.search(pattern, text))
            

def main(args=None):
    rclpy.init(args=args)
    node = SkillsOperator()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()