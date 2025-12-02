import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
from sensor_msgs.msg import JointState

from hand_control_msgs.msg import HandCommand, JointCommand
import hand_controller.utils as utils


class JointPolicy:
    def __init__(self, joint_name, limit):
        self.joint_name = joint_name
        self.limit = {
            'lower': limit[0],
            'upper': limit[1],
        }

        self.state = {
            'position': 0.0,
            'velocity': 0.0,
            'current': 0.0,
            'command': 0.0
        }


    def update_state(self, position, velocity, current):
        self.state['position'] = position
        self.state['velocity'] = velocity
        self.state['current'] = current

    def to_joint_position_command(self):
        command = JointCommand()
        command.joint = self.joint_name
        command.value = self.state['command']
        return command
    
    def to_joint_torque_command(self):
        command = JointCommand()
        command.joint = self.joint_name
        if self.state['position'] < self.limit['lower'] or self.state['position'] > self.limit['upper']:
            command.value = self.state['position']
        else:
            command.value =  self.state['position'] + 0.2 * (-self.state['position'] + self.limit['upper'])

        self.state['command'] = command.value
        return command


class BasicGraspingPolicy(Node):
    def __init__(self):
        super().__init__('basic_grasping_policy')
        self.state = 'open' # open/ grasp

        self.joint_policies = {
            'thumb_mcp': JointPolicy('thumb_mcp', [-20.0, 30.0]),
            'thumb_abd': JointPolicy('thumb_abd', [-20, 30]),
            'thumb_pip': JointPolicy('thumb_pip', [0.0, 80.0]),
            'thumb_dip': JointPolicy('thumb_dip', [0.0, 80.0]),
            'index_abd': JointPolicy('index_abd', [-30.0, 30.0]),
            'index_mcp': JointPolicy('index_mcp', [0.0, 60.0]),
            'index_pip': JointPolicy('index_pip', [0.0, 80.0]),
            'middle_abd': JointPolicy('middle_abd', [-30.0, 30.0]),
            'middle_mcp': JointPolicy('middle_mcp', [0.0, 60.0]),
            'middle_pip': JointPolicy('middle_pip', [0.0, 80.0]),
            'ring_abd': JointPolicy('ring_abd', [-30.0, 30.0]),
            'ring_mcp': JointPolicy('ring_mcp', [0.0, 60.0]),
            'ring_pip': JointPolicy('ring_pip', [0.0, 90.0]),
            'pinky_abd': JointPolicy('pinky_abd', [-30.0, 30.0]),
            'pinky_mcp': JointPolicy('pinky_mcp', [0.0, 60.0]),
            'pinky_pip': JointPolicy('pinky_pip', [0.0, 90.0]),
            'wrist': JointPolicy('wrist', [-10.0, 20.0])
        }

        self.position_joints = ['thumb_abd', 'index_abd', 'middle_abd', 'ring_abd', 'pinky_abd']
        self.torque_joints = ['thumb_mcp', 'thumb_pip', 'thumb_dip', 'index_mcp', 'index_pip',
                              'middle_mcp', 'middle_pip', 'ring_mcp', 'ring_pip',
                              'pinky_mcp', 'pinky_pip', 'wrist']

        self.command_publisher = self.create_publisher(
            HandCommand, 
            'hand_command', 
            10
        )

        self.control_srv = self.create_service(Trigger, 'grasp_control', self.grasp_trigger_callback)
        self.hand_joint_states_subscription = self.create_subscription(
            JointState,
            'hand_joint_states',
            self.joint_state_callback,
            10
        )

        self.get_logger().info('BasicGraspingPolicy node has been started.')

    def grasp_trigger_callback(self, request, response):
        if self.state == 'open':
            self.state = 'grasp'
            response.success = True
            response.message = "Grasping hand."
            self.get_logger().info(response.message)
        elif self.state == 'grasp':
            self.state = 'open'
            response.success = True
            response.message = "Opening hand."
            self.get_logger().info(response.message)
        else:
            response.success = False
            response.message = "Invalid state."
        
        return response
    
    def joint_state_callback(self, msg: JointState):
        for index in range(len(msg.name)):
            joint = msg.name[index]
            if joint in self.joint_policies:
                self.joint_policies[joint].update_state(
                    msg.position[index],
                    msg.velocity[index],
                    msg.effort[index]
                )
        if self.state == "open":
            self._publish_open_command()

        if self.state != 'grasp':
            return
        
        # Publish joint position commands
        hand_command = HandCommand()
        hand_command.mode = HandCommand.POSITION
        hand_command.joint_commands = []

        for joint_name in self.position_joints:
            joint_command = self.joint_policies[joint_name].to_joint_position_command()
            hand_command.joint_commands.append(joint_command)

        self.command_publisher.publish(hand_command)

        # Publish joint torque commands
        # hand_command.mode = HandCommand.TORQUE
        hand_command.joint_commands = []

        for joint_name in self.torque_joints:
            joint_command = self.joint_policies[joint_name].to_joint_torque_command()
            hand_command.joint_commands.append(joint_command)

        self.command_publisher.publish(hand_command)

    def _publish_open_command(self):
        self.command_publisher.publish(utils.create_open_hand_command())

def main(args=None):
    rclpy.init(args=args)
    node = BasicGraspingPolicy()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()