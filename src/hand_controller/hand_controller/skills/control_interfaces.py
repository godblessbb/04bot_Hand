
from hand_control_msgs.msg import ObjectList, HandCommand, JointCommand
# from aubo_msgs.srv import SetPoseStampedGoal
from jaka_msgs.srv import SetPoseStampedGoal
import tf_transformations
import time
from geometry_msgs.msg import PoseStamped

import threading

def call_arm_goal(node, eef_position, eef_orientation, end_effector_goal_client, constraints=[]):
    
    pose = PoseStamped()
    pose.header.frame_id = "world"
    pose.header.stamp = node.get_clock().now().to_msg()
    pose.pose.position.x = float(eef_position[0])
    pose.pose.position.y = float(eef_position[1])
    pose.pose.position.z = float(eef_position[2])

    qx, qy, qz, qw = tf_transformations.quaternion_from_euler(*eef_orientation)
    pose.pose.orientation.x = float(qx)
    pose.pose.orientation.y = float(qy)
    pose.pose.orientation.z = float(qz)
    pose.pose.orientation.w = float(qw)
    node.get_logger().info(f"Manipulate to {pose.pose.position}, {pose.pose.orientation}")
    # Call the service
    req = SetPoseStampedGoal.Request()
    req.goal = pose
    req.speed_factor = 0.1
    req.defined_constraints = constraints

    while not end_effector_goal_client.wait_for_service(timeout_sec=1.0):
        print('Waiting for end effector goal service...', flush=True)

    done_event = threading.Event()

    def _arm_goal_response(future):
        try:
            result = future.result()
            if result is not None:
                print("End effector goal sent successfully.", flush=True)
            else:
                print("Failed to send end effector goal.", flush=True)
        except Exception as e:
            print(f"Service call failed: {e}", flush=True)
        done_event.set()
    
    future = end_effector_goal_client.call_async(req)
    future.add_done_callback(_arm_goal_response)

    done_event.wait()

def publish_finger_command(node, finger_positions, command_type, publisher,  wrist_position=-10):
    msg = HandCommand()
    msg.mode = command_type
    msg.joint_commands = [
        JointCommand(joint='index_pip', value=float(finger_positions[0])),
        JointCommand(joint='index_mcp', value=float(finger_positions[1])),
        # JointCommand(joint='index_abd', value=float(finger_positions[2])),
        # JointCommand(joint='middle_abd', value=float(finger_positions[3])),
        JointCommand(joint='middle_pip', value=float(finger_positions[4])),
        JointCommand(joint='pinky_mcp', value=float(finger_positions[5])),
        JointCommand(joint='pinky_pip', value=float(finger_positions[6])),
        # JointCommand(joint='pinky_abd', value=float(finger_positions[7])),
        JointCommand(joint='middle_mcp', value=float(finger_positions[8])),
        JointCommand(joint='ring_pip', value=float(finger_positions[9])),
        JointCommand(joint='ring_mcp', value=float(finger_positions[10])),
        # JointCommand(joint='ring_abd', value=float(finger_positions[11])),
        JointCommand(joint='thumb_pip', value=float(finger_positions[12])),
        JointCommand(joint='thumb_dip', value=float(finger_positions[13])),
        JointCommand(joint='thumb_abd', value=float(finger_positions[14])),
        JointCommand(joint='thumb_mcp', value=float(finger_positions[15] - 40.0)),
    ]
    if command_type == HandCommand.POSITION:
        msg.joint_commands.append(
            JointCommand(joint='wrist', value=float(wrist_position)),
        )

    publisher.publish(msg)