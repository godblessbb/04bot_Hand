# import rclpy
# from rclpy.node import Node
# from hand_control_msgs.msg import HandCommand, JointCommand
# import time

# # 每个关节测试角度
# TEST_POSITIONS = {
#     'thumb_mcp': [40.0, -40.0],
#     'thumb_pip': [90.0, 0.0],
#     'thumb_dip': [100.0, -10.0],
#     'index_mcp': [90.0, -10.0],
#     'index_pip': [100.0, -10.0],
#     'middle_mcp': [80.0, -10.0],
#     'middle_pip': [100.0, -10.0],
#     'ring_mcp': [80.0, -10.0],
#     'ring_pip': [100.0, -10.0],
#     'pinky_abd': [20.0, 0.0],
#     'pinky_mcp': [20.0, 0.0],
#     'pinky_pip': [100.0, -10.0],
#     'wrist': [30.0, -40.0]
# }

# class JointTest(Node):
#     def __init__(self):
#         super().__init__('joint_test')
#         self.publisher_ = self.create_publisher(HandCommand, 'hand_command', 10)
#         self.failed_joints = []

#     def test_joint(self, joint_name, positions):
#         self.get_logger().info(f'Testing joint: {joint_name}')
#         moved = False
#         for pos in positions:
#             msg = HandCommand()
#             msg.mode = HandCommand.POSITION
#             msg.joint_commands = [JointCommand(joint=joint_name, value=pos)]
#             self.publisher_.publish(msg)
#             self.get_logger().info(f'Sent {joint_name} -> {pos}')
#             time.sleep(5)  # 等待动作
#         # 人工确认是否动作
#         while True:
#             response = input(f"Joint {joint_name} 是否动作？(y/n): ").strip().lower()
#             if response == 'y':
#                 moved = True
#                 break
#             elif response == 'n':
#                 moved = False
#                 break
#             else:
#                 print("请输入 y 或 n")
#         if not moved:
#             self.failed_joints.append(joint_name)
#         self.get_logger().info(f'Finished testing joint: {joint_name}\n')

#     def run_test(self):
#         for joint, positions in TEST_POSITIONS.items():
#             self.test_joint(joint, positions)
#         if self.failed_joints:
#             print("⚠️ 以下关节未动作：", self.failed_joints)
#         else:
#             print("✅ 所有关节动作正常")

# def main(args=None):
#     rclpy.init(args=args)
#     node = JointTest()
#     node.run_test()
#     rclpy.shutdown()

# if __name__ == '__main__':
#     main()
#!/usr/bin/env python3
import rclpy, time
from rclpy.node import Node
from hand_control_msgs.msg import HandCommand, JointCommand

class TestRingMCP(Node):
    def __init__(self):
        super().__init__('test_ring_mcp')
        self.pub = self.create_publisher(HandCommand, 'hand_command', 10)
        time.sleep(0.5)
        self.step_test()

    def send(self, name, val):
        msg = HandCommand()
        msg.mode = HandCommand.POSITION
        msg.joint_commands = [JointCommand(joint=name, value=float(val))]
        self.pub.publish(msg)
        self.get_logger().info(f'set {name} -> {val}')

    def step_test(self):
        # 先给一个全张开（可选）
        self.send('ring_mcp', 20); time.sleep(1.0)
        for v in [30, 40, 50, 60,70,80,90]:
            self.send('ring_mcp', v)
            time.sleep(1.0)
        # 反向回退
        for v in [80,70,60,50, 40, 30, 20]:
            self.send('ring_mcp', v)
            time.sleep(0.5)
        self.get_logger().info('done')

def main():
    rclpy.init()
    node = TestRingMCP()
    rclpy.spin_once(node, timeout_sec=0.1)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()