# import rclpy
# from rclpy.node import Node
# from std_srvs.srv import Trigger
# from std_msgs.msg import String
# from sensor_msgs.msg import JointState

# from hand_control_msgs.msg import HandCommand, JointCommand
# import hand_controller.utils as utils

# import json
# import time

# GESTURE_DICT_PATH = '/home/brad/AI_hand/robot_data.json'

# class NumberGesture(Node):
#     def __init__(self):
#         super().__init__('number_gesture')

#         self.gesture_dict = utils.load_json(GESTURE_DICT_PATH)

#         self.hand_command_publisher = self.create_publisher(HandCommand, 'hand_command', 10)

#         self.command_subscription = self.create_subscription(
#             String,
#             'voice_commands',
#             self.command_callback,
#             1
#         )

#     def command_callback(self, msg):
#         command = msg.data
#         try:
#             command_list = json.loads(command)
#             if not isinstance(command_list, list):
#                 self.get_logger().error("Parsed command is not a list.")
#                 return
#         except json.JSONDecodeError as e:
#             self.get_logger().error(f"Failed to decode JSON: {e}")
#             return
        
#         action = command_list[0].get('action', None)
#         if action is None:
#             self.get_logger().error("No action found in command.")
#             return
        
#         for gesture in self.gesture_dict:
#             if gesture.get('action') == action:
#                 self.publish_hand_command(gesture)
#                 return

    
#     def publish_hand_command(self, gesture):
#         hand_command = utils.create_open_hand_command()
#         self.hand_command_publisher.publish(hand_command)

#         time.sleep(1)

#         hand_command.joint_commands = [
#             JointCommand(joint='index_pip', value=gesture["finger_positions"][0]),
#             JointCommand(joint='index_mcp', value=gesture["finger_positions"][1]),
#             JointCommand(joint='index_abd', value=gesture["finger_positions"][2]),
#             JointCommand(joint='middle_abd', value=gesture["finger_positions"][3]),
#             JointCommand(joint='middle_pip', value=gesture["finger_positions"][4]),
#             JointCommand(joint='pinky_mcp', value=gesture["finger_positions"][5]),
#             JointCommand(joint='pinky_pip', value=gesture["finger_positions"][6]),
#             JointCommand(joint='pinky_abd', value=gesture["finger_positions"][7]),
#             JointCommand(joint='middle_mcp', value=gesture["finger_positions"][8]),
#             JointCommand(joint='ring_pip', value=gesture["finger_positions"][9]),
#             JointCommand(joint='ring_mcp', value=gesture["finger_positions"][10]),
#             JointCommand(joint='ring_abd', value=gesture["finger_positions"][11]),
#             JointCommand(joint='thumb_pip', value=gesture["finger_positions"][12]),
#             JointCommand(joint='thumb_dip', value=gesture["finger_positions"][13]),
#             JointCommand(joint='thumb_abd', value=gesture["finger_positions"][14]),
#             JointCommand(joint='thumb_mcp', value=gesture["finger_positions"][15]),
#             JointCommand(joint='wrist', value=gesture["finger_positions"][16])
#         ]
        
#         self.hand_command_publisher.publish(hand_command)
#         self.get_logger().info(f"Published hand command for action: {gesture.get('action')}")

# def main(args=None):
#     rclpy.init(args=args)
#     node = NumberGesture()
#     try:
#         rclpy.spin(node)
#     except KeyboardInterrupt:
#         pass
#     finally:
#         node.destroy_node()
#         rclpy.shutdown()

# if __name__ == '__main__':
#     main()
#!/usr/bin/env python3

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rclpy
from rclpy.node import Node
import threading
import time

from hand_control_msgs.msg import HandCommand, JointCommand
import hand_controller.utils as utils


class NumberGesture(Node):
    def __init__(self):
        super().__init__('number_gesture_keyboard')

        # 1. 手势库：你在这里手动定义 1~10 的手势关节角度（单位和你的手一致，通常是角度/期望位置）
        #
        # 每个手势是一个长度为 17 的列表，对应下面这个顺序：
        # 0  index_pip
        # 1  index_mcp
        # 2  index_abd
        # 3  middle_abd
        # 4  middle_pip
        # 5  pinky_mcp
        # 6  pinky_pip
        # 7  pinky_abd
        # 8  middle_mcp
        # 9  ring_pip
        # 10 ring_mcp
        # 11 ring_abd
        # 12 thumb_pip
        # 13 thumb_dip
        # 14 thumb_abd
        # 15 thumb_mcp
        # 16 wrist
        #
        # TODO: 你需要把这些示例值改成对你机械手真正有效的值。
        # 比如 "1" 的意思是：食指竖起来，其它手指弯下；"2" 就是食指+中指竖起；以此类推。
        # 这些值现在是示意占位，不会伤手，但可能也不会是你想要的姿势。请按你机器的角度表去填。

        self.gesture_dict = {
           
     "1":  [ 20,  20,  0,   0, 150, 150,150, 30, 150,150,  90, 30, 100,100,30,100, 0],
    "2":  [ 20,  20,  0,   0,  20, 150,150, 30,  20,150,  90, 30, 100,100,30,100, 0],
    "3":  [ 20,  20,  0,   0,  20,  20, 20, 30,  20,150,  90, 30, 100,100,30,100, 0],
    "4":  [ 20,  20,  0,   0,  20,  20, 20, 30,  20, 20,  -15, 30, 100,100,30,100, 0],
    "5":  [ 20,  20, 30,  30,  20,  20, 20, 30,  20, 20, -15, 30,  20, 20,30, 20, 0],  # 张开：-15
    "6":  [150,150,  0,   0, 150,  20, 20, 30, 150,150,  90, 30,  20, 20,80, 20, 0],
    "7":  [100,100,  0,   0, 100, 150,150,30, 100,150,  90, 30, 100,100,30,100, 0],
    "8":  [ 20,  20,  0,   0, 100, 150,150,30, 150,150,  90, 30,  20, 20,20, 20, 0],
    "9":  [60,20,  0,   0, 150, 150,150,30, 150,150,  90, 30, 150,150,30,150, 0],
    "10": [150,150,  0,   0, 150, 150,150,30, 150,150,  90, 30, 150,150,30,150, 0],
        }

        # 2. Publisher: 发送控制手的消息
        self.hand_command_publisher = self.create_publisher(
            HandCommand,
            'hand_command',
            10
        )

        # 3. 启动一个后台线程，循环读取你在终端输入的数字
        self.input_thread = threading.Thread(
            target=self.input_loop,
            daemon=True
        )
        self.input_thread.start()

        # self.command_subscription = self.create_subscription(
        #     String,
        #     'voice_commands',
        #     self.command_callback,
        #     1
        # )

    def command_callback(self, msg):
        command = msg.data
        try:
            command_list = json.loads(command)
            if not isinstance(command_list, list):
                self.get_logger().error("Parsed command is not a list.")
                return
        except json.JSONDecodeError as e:
            self.get_logger().error(f"Failed to decode JSON: {e}")
            return
        
        action = command_list[0].get('action', None)
        if action is None:
            self.get_logger().error("No action found in command.")
            return
        
        for gesture in self.gesture_dict:
            if gesture.get('action') == action:
                self.publish_hand_command(gesture)
                return


    def input_loop(self):
        """
        循环等待你在终端里输入手势编号。
        你可以输入: 1 / 2 / ... / 10
        输入 q 退出。
        """
        self.get_logger().info("数字手势控制已启动。请输入 1~10，或 q 退出。")

        while rclpy.ok():
            try:
                user_in = input("请输入数字手势 (1~10): ").strip()
            except EOFError:
                self.get_logger().warn("输入通道结束。停止手势输入线程。")
                break

            if user_in == "":
                continue

            if user_in.lower() in ["q", "quit", "exit"]:
                self.get_logger().info("收到退出命令，关闭节点。")
                rclpy.shutdown()
                break

            if user_in not in self.gesture_dict:
                self.get_logger().warn(f"没有定义手势 {user_in}，请输 1~10 或 q 退出。")
                continue

            self.perform_number_gesture(user_in)


    def perform_number_gesture(self, number_key: str):
        """
        根据 number_key ('1', '2', ... '10') 从 GESTURES 里取角度，
        先张开手（防止卡住），然后发目标关节值。
        """
        self.get_logger().info(f"执行手势 {number_key}")

        # 第一步：张开手
        # 假设 utils.create_open_hand_command() 会发送一个全张开的 HandCommand
        # 如果你没有这个函数，下面可以直接跳过
        try:
            open_cmd = utils.create_open_hand_command()
            self.hand_command_publisher.publish(open_cmd)
            time.sleep(0.5)
        except Exception as e:
            self.get_logger().warn(f"create_open_hand_command 调用失败，继续直接发目标手势: {e}")

        # 第二步：根据 GESTURES[number_key] 设置每个关节
        fp = self.gesture_dict[number_key]

        hand_command = HandCommand()
        hand_command.mode = HandCommand.POSITION  # 用位置控制模式

        hand_command.joint_commands = [
            JointCommand(joint='index_pip',   value=float(fp[0])),
            JointCommand(joint='index_mcp',   value=float(fp[1])),
            JointCommand(joint='index_abd',   value=float(fp[2])),
            JointCommand(joint='middle_abd',  value=float(fp[3])),
            JointCommand(joint='middle_pip',  value=float(fp[4])),
            JointCommand(joint='pinky_mcp',   value=float(fp[5])),
            JointCommand(joint='pinky_pip',   value=float(fp[6])),
            JointCommand(joint='pinky_abd',   value=float(fp[7])),
            JointCommand(joint='middle_mcp',  value=float(fp[8])),
            JointCommand(joint='ring_pip',    value=float(fp[9])),
            JointCommand(joint='ring_mcp',    value=float(fp[10])),
            JointCommand(joint='ring_abd',    value=float(fp[11])),
            JointCommand(joint='thumb_pip',   value=float(fp[12])),
            JointCommand(joint='thumb_dip',   value=float(fp[13])),
            JointCommand(joint='thumb_abd',   value=float(fp[14])),
            JointCommand(joint='thumb_mcp',   value=float(fp[15])),
            JointCommand(joint='wrist',       value=float(fp[16])),
        ]

        # 真正发送
        self.hand_command_publisher.publish(hand_command)
        self.get_logger().info(f"手势 {number_key} 已发布。")


def main(args=None):
    rclpy.init(args=args)
    node = NumberGesture()  # 创建 ROS2 节点
    try:
        rclpy.spin(node)    # 让 ROS2 一直运行
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()