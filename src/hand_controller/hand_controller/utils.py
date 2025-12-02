from hand_control_msgs.msg import HandCommand, JointCommand
import json

def create_open_hand_command():
    """Create a HandCommand message to open the hand."""
    msg = HandCommand()
    msg.mode = HandCommand.POSITION
    msg.joint_commands = [
        JointCommand(joint='thumb_mcp', value=-20.0),
        JointCommand(joint='thumb_abd', value=0.0),
        JointCommand(joint='thumb_pip', value=0.0),
        JointCommand(joint='thumb_dip', value=0.0),
        JointCommand(joint='index_abd', value=0.0),
        JointCommand(joint='index_mcp', value=0.0),
        JointCommand(joint='index_pip', value=0.0),
        JointCommand(joint='middle_abd', value=0.0),
        JointCommand(joint='middle_mcp', value=0.0),
        JointCommand(joint='middle_pip', value=0.0),
        JointCommand(joint='ring_abd', value=0.0),
        JointCommand(joint='ring_mcp', value=0.0),
        JointCommand(joint='ring_pip', value=0.0),
        JointCommand(joint='pinky_abd', value=0.0),
        JointCommand(joint='pinky_mcp', value=0.0),
        JointCommand(joint='pinky_pip', value=0.0),
        JointCommand(joint='wrist', value=-10.0)
    ]

    return msg

def load_json(file_path):
    """Load a JSON file and return its content as dict."""
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {file_path}: {e}")
        return {}