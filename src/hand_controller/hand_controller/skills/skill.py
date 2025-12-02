from abc import ABC, abstractmethod
from rclpy.node import Node

class Skill(ABC):
    def __init__(self, node):
        self.node = node
        self.STEPS_ORDER = {}
        self.last_goal = {
            'position': [0.0, 0.0, 0.0],
            'orientation': [0.0, 0.0, 0.0]
        }

    @abstractmethod
    def execute(self, step, target_point):
        pass