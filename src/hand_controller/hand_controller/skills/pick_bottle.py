#!/usr/bin/env python3

from rclpy.node import Node
import time
from hand_controller.models.robot_state import *
from hand_control_msgs.msg import HandCommand
from aubo_msgs.srv import SetPoseStampedGoal
from hand_controller.skills.control_interfaces import call_arm_goal, publish_finger_command
from hand_controller.skills.skill import Skill

class PickBottle(Skill):
    def __init__(self, node, end_effector_goal_client, hand_command_publisher):
        super().__init__(node)
        self.end_effector_goal_client = end_effector_goal_client
        self.hand_command_publisher = hand_command_publisher

        self.STEPS_ORDER = {
            'approach_above': self.approach_above,
            'approach': self.approach,
            'move_forward': self.move_forward,
            'grasp': self.grasp,
            'lift': self.lift
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
    def approach_above(self, target_point):
        _approach_vector = [0.05 * x for x in self._approach_vector(target_point)]
        approach_point = [target_point[0] - _approach_vector[0]  + 0.03, target_point[1] - _approach_vector[1], target_point[2] +0.15]
        approach_rpy = [np.pi / 2, 0.0, np.arctan2(_approach_vector[1], _approach_vector[0])]
        self.last_goal['position'] = approach_point
        self.last_goal['orientation'] = approach_rpy
        call_arm_goal(self.node, approach_point, approach_rpy, self.end_effector_goal_client,
                      constraints=[
                      ])

    def approach(self, target_point):
        _approach_vector = [0.1 * x for x in self._approach_vector(target_point)]
        approach_point = [target_point[0] - _approach_vector[0]  + 0.03, target_point[1] - _approach_vector[1], target_point[2] - 0.02]
        approach_rpy = [np.pi / 2, 0.0, np.arctan2(_approach_vector[1], _approach_vector[0])]
        self.last_goal['position'] = approach_point
        self.last_goal['orientation'] = approach_rpy
        call_arm_goal(self.node, approach_point, approach_rpy, self.end_effector_goal_client,
                      constraints=[
                      ])
        
        # Open the palm
        finger_positions = [0.0] * 16
        publish_finger_command(self.node, finger_positions, HandCommand.POSITION, self.hand_command_publisher)
        time.sleep(5.0)
        
    def move_forward(self, target_point):
        _approach_vector = [0.01 * x for x in self._approach_vector(target_point)]
        approach_point = [target_point[0] - _approach_vector[0] + 0.03, target_point[1] - _approach_vector[1], target_point[2] - 0.02]
        approach_rpy = [np.pi / 2, 0.0, np.arctan2(_approach_vector[1], _approach_vector[0])]
        self.last_goal['position'] = approach_point
        self.last_goal['orientation'] = approach_rpy
        call_arm_goal(self.node, approach_point, approach_rpy, self.end_effector_goal_client,
                      constraints=[
                          SetPoseStampedGoal.Request.KEEP_EEF_Y_UP,
                      ])
        
    def grasp(self, target_point):
        # Close the palm
        finger_positions = [100.0, 150.0, 0.0, 0.0,
                            100.0, 150.0, 100.0,
                            0.0, 150.0, 100.0,
                            30.0, 100.0, 150.0,
                            150.0, 0.0, 150.0]
        publish_finger_command(self.node, finger_positions, HandCommand.TORQUE, self.hand_command_publisher)
        # Wait for a moment to ensure the grasp is complete
        time.sleep(3.0)
        
    def lift(self, target_point):        
        self.last_goal['position'][2] += 0.2
        call_arm_goal(self.node, self.last_goal['position'], self.last_goal['orientation'], self.end_effector_goal_client,
                      constraints=[
                          SetPoseStampedGoal.Request.KEEP_EEF_Y_UP,
                      ])
