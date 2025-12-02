#!/usr/bin/env python3

from rclpy.node import Node
import time
from hand_controller.models.robot_state import *
from hand_control_msgs.msg import HandCommand
from aubo_msgs.srv import SetPoseStampedGoal
from hand_controller.skills.control_interfaces import call_arm_goal, publish_finger_command
from hand_controller.skills.skill import Skill

class PlaceBottle(Skill):
    def __init__(self, node, end_effector_goal_client, hand_command_publisher):
        super().__init__(node)
        self.end_effector_goal_client = end_effector_goal_client
        self.hand_command_publisher = hand_command_publisher

        self.STEPS_ORDER = {
            'approach': self.approach,
            'move_down': self.move_down,
            'open': self.open,
            'move_back': self.move_back
        }
        
    def execute(self, step, target_point):
        return self.STEPS_ORDER[step](target_point)
    
    
    def _approach_vector(self, target_point):
        vect_angle = np.arctan2(target_point[1], target_point[0])
        dist = np.hypot(target_point[1], target_point[0])
        vect_angle += np.pi / 4
        vect_angle -= (np.pi / 4) * min(0.5, dist)
        vect_angle += np.pi / 2
        return [np.cos(vect_angle), np.sin(vect_angle), 0.0]

        
    """
    Steps for pick bottle
    """
    def approach(self, target_point):
        _approach_vector = [0.001 * x for x in self._approach_vector(target_point)]
        approach_point = [target_point[0] - _approach_vector[0], target_point[1] - _approach_vector[1], target_point[2] + 0.1]
        approach_rpy = [np.pi / 2, 0.0, np.arctan2(_approach_vector[1], _approach_vector[0])]
        self.last_goal['position'] = approach_point
        self.last_goal['orientation'] = approach_rpy
        call_arm_goal(self.node, approach_point, approach_rpy, self.end_effector_goal_client,
                      constraints=[
                          SetPoseStampedGoal.Request.KEEP_EEF_Y_UP,
                      ])
        
        
    def move_down(self, target_point):
        _approach_vector = [0.001 * x for x in self._approach_vector(target_point)]
        approach_point = [target_point[0] - _approach_vector[0], target_point[1] - _approach_vector[1], target_point[2]]
        approach_rpy = [np.pi / 2, 0.0, np.arctan2(_approach_vector[1], _approach_vector[0])]
        self.last_goal['position'] = approach_point
        self.last_goal['orientation'] = approach_rpy
        call_arm_goal(self.node, approach_point, approach_rpy, self.end_effector_goal_client,
                      constraints=[
                      ])
        
        
    def open(self, target_point):
        # Open the palm
        # Open the palm
        finger_positions = [0.0] * 16
        publish_finger_command(self.node, finger_positions, HandCommand.POSITION, self.hand_command_publisher)
        # Wait for a moment to ensure the open is complete
        time.sleep(3.0)
        
    def move_back(self, target_point):        
        self.last_goal['position'][2] += 0.2
        call_arm_goal(self.node, self.last_goal['position'], self.last_goal['orientation'], self.end_effector_goal_client,
                      constraints=[
                      ])
