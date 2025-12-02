import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from hand_control_msgs.msg import HandCommand
from sensor_msgs.msg import JointState

from orca_hand_hardware_interface.core import OrcaHand

MODE_MAP = {
    HandCommand.DISABLE: 'position',
    HandCommand.ENABLE: 'position',
    HandCommand.POSITION: 'current_based_position',
    HandCommand.VELOCITY: 'velocity',
    HandCommand.TORQUE: 'current',
}

class HandControllerNode(Node):
    def __init__(self):
        super().__init__('hand_controller_node')
        
        self.current_command_mode = HandCommand.DISABLE  # Default command mode
        self.prev_positions = None

        # Read configuration
        self.declare_parameter('config_folder', '')
        config_folder = self.get_parameter('config_folder').get_parameter_value().string_value
        self.get_logger().info(f'Configured folder: {config_folder}')

        if not config_folder:
            self.get_logger().error('No config folder specified. Exiting...')
            rclpy.shutdown()
            return
        
        # Initialize OrcaHand core controller
        self.orca_hand = OrcaHand(config_folder)
        status = self.orca_hand.connect()
        self.get_logger().info(f'{status}')
        if not status[0]:
            self.get_logger().fatal("Failed to connect to the hand.")
            rclpy.shutdown()
            return
        
        # Temporarily disable torque to collect data
        # self.orca_hand.disable_torque()
        # self.orca_hand.enable_torque([0])

        # Enable torques for control
        self.orca_hand.enable_torque()

        # Publishers
        self.joint_states_publisher = self.create_publisher(
            JointState,
            'hand_joint_states',
            1
        )

        # Initalize callbacks
        self.time_step = 0.2    # 5Hz
        self.pos_reading_timer = self.create_timer(
            self.time_step,
            self.read_position_callback
        )

        self.command_subscription = self.create_subscription(
            HandCommand,
            'hand_command',
            self.command_callback,
            10
        )

    
    def read_position_callback(self):
        joint_positions = self.orca_hand.get_joint_pos(False)
        joint_currents = self.orca_hand.get_joint_current(False)
        joint_states = JointState()
        joint_states.header.stamp = self.get_clock().now().to_msg()
        for joint in joint_positions.keys():
            joint_states.name.append(joint)
            joint_states.position.append(joint_positions[joint])
            joint_states.effort.append(joint_currents[joint])

            if self.prev_positions is None:
                joint_states.velocity.append(0.0)
            else:
                joint_states.velocity.append((joint_positions[joint] - self.prev_positions[joint]) / self.time_step)
        
        self.prev_positions = joint_positions
        self.joint_states_publisher.publish(joint_states)

    def command_callback(self, msg):
        if msg.mode != self.current_command_mode:
            self.get_logger().debug(f'Switch to new mode: {msg.mode}')
            self.orca_hand.set_control_mode(MODE_MAP[msg.mode])
            self.current_command_mode = msg.mode

        if msg.mode == HandCommand.POSITION:
            joint_dict = {joint_command.joint: joint_command.value for joint_command in msg.joint_commands}
            self.orca_hand.set_joint_pos(joint_dict, 3, 0.01)
            self.get_logger().info(f'Set joint positions: {joint_dict}')

        elif msg.mode == HandCommand.TORQUE:
            joint_dict = {joint_command.joint: joint_command.value for joint_command in msg.joint_commands}
            self.orca_hand.set_joint_torque(joint_dict)
            self.get_logger().debug(f'Set joint torques: {joint_dict}')

        

def main(args=None):
    rclpy.init(args=args)
    node = HandControllerNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down HandControllerNode...')
    finally:
        node.orca_hand.disable_torque()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()