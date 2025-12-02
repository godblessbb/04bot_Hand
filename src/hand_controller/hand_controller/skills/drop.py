#!/usr/bin/env python3

from rclpy.node import Node
import tf_transformations
from hand_controller.models.robot_state import *
from hand_control_msgs.msg import HandCommand
from aubo_msgs.srv import SetPoseStampedGoal
from hand_controller.skills.control_interfaces import call_arm_goal, publish_finger_command
from hand_controller.skills.skill import Skill
import numpy as np
import time

class Drop(Skill):
    def __init__(self, node, end_effector_goal_client, hand_command_publisher):
        super().__init__(node)
        self.end_effector_goal_client = end_effector_goal_client
        self.hand_command_publisher = hand_command_publisher

        self.STEPS_ORDER = {
            'approach': self.approach, 
            'open': self.open,
        }
        
    def execute(self, step, target_point):
        return self.STEPS_ORDER[step](target_point)
    
    
    def _approach_vector(self, target_point):
        vect_angle = np.arctan2(target_point[1], target_point[0])
        dist = np.hypot(target_point[1], target_point[0])
        vect_angle += np.pi / 2 - max(1.0, 1.0 - dist) * np.pi / 4
        return [np.cos(vect_angle), np.sin(vect_angle), 0.0]

    
    def do_rotation_rpy(self, rpy, angle):
        r = tf_transformations.euler_matrix(rpy[0], rpy[1], rpy[2])
        rot_x = tf_transformations.euler_matrix(angle, 0, 0)
        new_mat = np.dot(r, rot_x)
        new_rpy = tf_transformations.euler_from_matrix(new_mat)
        return new_rpy

        
    """
    Steps for drop object
    """
    def approach(self, target_point):
        target_point[1] -= 0.03 * np.sign(target_point[1])
        _approach_vector = self._approach_vector(target_point)
        approach_point = [target_point[0], target_point[1], target_point[2] + 0.25]
        approach_rpy = [0.0, np.pi / 2, np.arctan2(_approach_vector[1], _approach_vector[0])]
        self.last_goal['position'] = approach_point
        self.last_goal['orientation'] = approach_rpy
        call_arm_goal(self.node, approach_point, approach_rpy, self.end_effector_goal_client)
        
        
    def open(self, target_point):
        # Open the palm
        finger_positions = [0.0] * 16
        publish_finger_command(self.node, finger_positions, HandCommand.POSITION, self.hand_command_publisher)
        # Wait for a moment to ensure the open is complete
        time.sleep(3.0)