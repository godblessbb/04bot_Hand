#!/usr/bin/env python3

from rclpy.node import Node
import time
from hand_controller.models.robot_state import *
from hand_control_msgs.msg import HandCommand
from aubo_msgs.srv import SetPoseStampedGoal
from hand_controller.skills.control_interfaces import call_arm_goal, publish_finger_command
from hand_controller.skills.skill import Skill

class PlaceCubeBall(Skill):
    def __init__(self, node, end_effector_goal_client, hand_command_publisher):
        super().__init__(node)
        self.end_effector_goal_client = end_effector_goal_client
        self.hand_command_publisher = hand_command_publisher

        self.STEPS_ORDER = {
            'approach': self.approach,
            'move_down': self.move_down,
            'open': self.open,
            'lift': self.lift
        }
        
    def execute(self, step, target_point):
        return self.STEPS_ORDER[step](target_point)

        
    """
    Steps for pick cube
    """
    def approach(self, target_point):
        approach_point = [target_point[0], target_point[1], target_point[2] + 0.2]
        approach_rpy = [0.0, np.pi, 0.0]
        self.last_goal['position'] = approach_point
        self.last_goal['orientation'] = approach_rpy
        call_arm_goal(self.node, approach_point, approach_rpy, self.end_effector_goal_client,
                      constraints=[
                      ])
        
    def move_down(self, target_point):
        approach_point = [target_point[0]+0.02, target_point[1], target_point[2] + 0.15]
        approach_rpy = [0.0, np.pi, 0.0]
        self.last_goal['position'] = approach_point
        self.last_goal['orientation'] = approach_rpy
        call_arm_goal(self.node, approach_point, approach_rpy, self.end_effector_goal_client,
                      constraints=[
                      ])
        
    def open(self, target_point):
        # Open the palm
        finger_positions = [0.0] * 16
        publish_finger_command(self.node, finger_positions, HandCommand.POSITION, self.hand_command_publisher)
        # Wait for a moment to ensure the open is complete
        time.sleep(3.0)
        
    def lift(self, target_point):        
        self.last_goal['position'][2] += 0.2
        call_arm_goal(self.node, self.last_goal['position'], self.last_goal['orientation'], self.end_effector_goal_client,
                      constraints=[
                      ])
