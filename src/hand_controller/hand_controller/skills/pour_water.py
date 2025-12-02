#!/usr/bin/env python3

from rclpy.node import Node
import tf_transformations
from hand_controller.models.robot_state import *
from hand_control_msgs.msg import HandCommand
from aubo_msgs.srv import SetPoseStampedGoal
from hand_controller.skills.control_interfaces import call_arm_goal, publish_finger_command
from hand_controller.skills.skill import Skill
import numpy as np

POUR_ANGLE = np.pi /2.3

class PourWater(Skill):
    def __init__(self, node, end_effector_goal_client, hand_command_publisher):
        super().__init__(node)
        self.end_effector_goal_client = end_effector_goal_client
        self.hand_command_publisher = hand_command_publisher

        self.STEPS_ORDER = {
            'approach': self.approach,
            'pour': self.pour,
            'retract': self.retract,
        }
        
    def execute(self, step, target_point):
        return self.STEPS_ORDER[step](target_point)
    
    
    def _approach_vector(self, target_point):
        vect_angle = np.arctan2(target_point[1], target_point[0])
        dist = np.hypot(target_point[1], target_point[0])
        vect_angle += np.pi / 2
        vect_angle -= (np.pi / 2) * min(0.5, dist) * 2
        vect_angle += np.pi / 2
        return [np.cos(vect_angle), np.sin(vect_angle), 0.0]
    
    def do_rotation_rpy(self, rpy, angle):
        r = tf_transformations.euler_matrix(rpy[0], rpy[1], rpy[2])
        rot_z = tf_transformations.euler_matrix(0, 0, -angle)
        new_mat = np.dot(r, rot_z)
        new_rpy = tf_transformations.euler_from_matrix(new_mat)
        return new_rpy

        
    """
    Steps for pour water into cup
    """
    def approach(self, target_point):
        _approach_vector = [0.1 * x for x in self._approach_vector(target_point)]
        _approach_vector2 = [_approach_vector[1], -_approach_vector[0], 0.0]
        print(f"Approach vector {_approach_vector}")
        print(f"Approach vector2 {_approach_vector2}")
        approach_point = [target_point[0] - _approach_vector[0] - _approach_vector2[0] + 0.02, 
                          target_point[1] - _approach_vector[1] - _approach_vector2[1], 
                          target_point[2] + 0.15]
        approach_rpy = [np.pi / 2, 0.0, np.arctan2(_approach_vector[1], _approach_vector[0])]

        call_arm_goal(self.node, approach_point, approach_rpy, self.end_effector_goal_client,
                      constraints=[
                          SetPoseStampedGoal.Request.KEEP_EEF_Y_UP,
                      ])
        
    def pour(self, target_point):
        dist_to_cup_x = 0.125
        dist_to_cup_y = 0.026 / dist_to_cup_x
        _pour_vector = [dist_to_cup_x * x for x in self._approach_vector(target_point)]
        _pour_vector2 = [dist_to_cup_y * _pour_vector[1], -dist_to_cup_y * _pour_vector[0], 0.0]
        pour_point = [target_point[0] - _pour_vector[0] - _pour_vector2[0] + 0.02, 
                      target_point[1] - _pour_vector[1] - _pour_vector2[1],
                      target_point[2] + 0.1]
        pour_rpy = self.do_rotation_rpy([np.pi / 2, 0.0, np.arctan2(_pour_vector[1], _pour_vector[0])], POUR_ANGLE)

        call_arm_goal(self.node, pour_point, pour_rpy, self.end_effector_goal_client,
                      constraints=[
                      ])

    def retract(self, target_point):
        _approach_vector = [0.1 * x for x in self._approach_vector(target_point)]
        approach_point = [target_point[0] - _approach_vector[0] + 0.03, target_point[1] - _approach_vector[1], target_point[2] + 0.2]
        approach_rpy = [np.pi / 2, 0.0, np.arctan2(_approach_vector[1], _approach_vector[0])]

        call_arm_goal(self.node, approach_point, approach_rpy, self.end_effector_goal_client,
                      constraints=[
                      ])
        