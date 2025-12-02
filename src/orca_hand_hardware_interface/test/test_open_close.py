import rclpy
from rclpy.node import Node
from hand_control_msgs.msg import HandCommand, JointCommand
import json
import time

class PositionTest(Node):
    def __init__(self):
        super().__init__('position_test')
        self.publisher_ = self.create_publisher(HandCommand, 'hand_command', 10)

    def run_test(self):
        # Open hand
        msg = HandCommand()
        msg.mode = HandCommand.POSITION
        msg.joint_commands = [
            # JointCommand(joint='thumb_mcp', value=-30.0),
            # JointCommand(joint='thumb_pip', value=0.0),
            # JointCommand(joint='thumb_dip', value=0.0),
            JointCommand(joint='index_abd', value=-30.0),
            # JointCommand(joint='index_mcp', value=0.0),
            # JointCommand(joint='index_pip', value=0.0),
            # JointCommand(joint='middle_abd', value=0.0),
            # JointCommand(joint='middle_mcp', value=0.0),
            # JointCommand(joint='middle_pip', value=0.0),
            # JointCommand(joint='ring_abd', value=10.0),
            # JointCommand(joint='ring_mcp', value=-20.0),
            # JointCommand(joint='ring_pip', value=0.0),
            # JointCommand(joint='pinky_abd', value=0.0),
            # JointCommand(joint='pinky_mcp', value=0.0),
            # JointCommand(joint='pinky_pip', value=0.0),
            #JointCommand(joint='wrist', value=30.0)
        ]
        
        self.get_logger().info('Published position command')

        for _ in range(50):
            self.publisher_.publish(msg)
            time.sleep(0.1)
        # Close hand by torque
        msg.mode = HandCommand.POSITION
        msg.joint_commands = [
            # JointCommand(joint='thumb_mcp', value=40.0),
            # JointCommand(joint='thumb_pip', value=60.0),
            # JointCommand(joint='thumb_dip', value=60.0),
            JointCommand(joint='index_abd', value=0.0),
            # JointCommand(joint='index_mcp', value=60.0),
            # JointCommand(joint='index_pip', value=80.0),
            # JointCommand(joint='middle_mcp', value=60.0),
            # JointCommand(joint='middle_pip', value=80.0),
            # JointCommand(joint='ring_mcp', value=30.0),
            # JointCommand(joint='ring_pip', value=80.0),
            # JointCommand(joint='pinky_mcp', value=60.0),
            # JointCommand(joint='pinky_pip', value=80.0),
            # JointCommand(joint='wrist', value=-10.0)
        ]
        self.get_logger().info('Published position command to close hand')

        for _ in range(50):
            self.publisher_.publish(msg)
            time.sleep(0.1)

def main(args=None):
    rclpy.init(args=args)
    node = PositionTest()
    node.run_test()

if __name__ == '__main__':
    main()