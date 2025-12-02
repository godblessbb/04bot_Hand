#!/usr/bin/env python3

from rclpy.node import Node
import time
from hand_controller.models.robot_state import *
from hand_control_msgs.msg import HandCommand
from aubo_msgs.srv import SetPoseStampedGoal
from hand_controller.skills.control_interfaces import call_arm_goal, publish_finger_command
from hand_controller.skills.skill import Skill

class PickBall(Skill):
    def __init__(self, node, end_effector_goal_client, hand_command_publisher):
        super().__init__(node)
        self.end_effector_goal_client = end_effector_goal_client
        self.hand_command_publisher = hand_command_publisher

        self.STEPS_ORDER = {
            'approach': self.approach,
            'move_down': self.move_down,
            'grasp': self.grasp,
            'lift': self.lift
        }
        
    def execute(self, step, target_point):
        return self.STEPS_ORDER[step](target_point)

    def _approach_vector(self, target_point):
        vect_angle = np.arctan2(target_point[1], target_point[0])
        dist = np.hypot(target_point[1], target_point[0])
        vect_angle += np.pi / 2 - max(1.0, 1.0 - dist) * np.pi / 4
        return [np.cos(vect_angle), np.sin(vect_angle), 0.0]

        
    """
    Steps for pick ball
    """
    def approach(self, target_point):
        target_point[0] += 0.02
        _approach_vector = [0.01 * x for x in self._approach_vector(target_point)]
        approach_point = [target_point[0] - _approach_vector[0], target_point[1] - _approach_vector[1], target_point[2] + 0.15]
        approach_rpy = [0.0, np.pi / 2, np.arctan2(_approach_vector[1], _approach_vector[0])]
        self.last_goal['position'] = approach_point
        self.last_goal['orientation'] = approach_rpy
        call_arm_goal(self.node, approach_point, approach_rpy, self.end_effector_goal_client,
                      constraints=[
                      ])
        
        # Open the palm
        finger_positions = [0.0] * 16
        finger_positions[15] = 40.0
        publish_finger_command(self.node, finger_positions, HandCommand.POSITION, self.hand_command_publisher, wrist_position=10.0)
        time.sleep(5.0)
            
                
    def move_down(self, target_point):
        target_point[0] += 0.01
        _approach_vector = [0.01 * x for x in self._approach_vector(target_point)]
        approach_point = [target_point[0] - _approach_vector[0], target_point[1] - _approach_vector[1], target_point[2] + 0.04] # Adjust grasping height
        approach_rpy = [0.0, np.pi / 2, np.arctan2(_approach_vector[1], _approach_vector[0])]
        self.last_goal['position'] = approach_point
        self.last_goal['orientation'] = approach_rpy
        call_arm_goal(self.node, approach_point, approach_rpy, self.end_effector_goal_client,
                      constraints=[
                      ])

    def grasp(self, target_point):
        # Close the palm
        finger_positions = [60.0, 60.0, 0.0, 0.0,
                            60.0, 60.0, 60.0,
                            0.0, 60.0, 60.0,
                            60.0, 0.0, 60.0,
                            55.0, 0.0, 60.0]
        publish_finger_command(self.node, finger_positions, HandCommand.TORQUE, self.hand_command_publisher)
        # Wait for a moment to ensure the grasp is complete
        time.sleep(3.0)
        
    def lift(self, target_point):        
        self.last_goal['position'][2] += 0.15
        call_arm_goal(self.node, self.last_goal['position'], self.last_goal['orientation'], self.end_effector_goal_client,
                      constraints=[
                      ])
