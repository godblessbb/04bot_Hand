from dataclasses import dataclass, field
from typing import List
import torch
import numpy as np
from scipy.spatial.transform import Rotation as R

DEG_TO_RAD = np.pi / 180.0

def encode_angles(rpy):
    """
    Encode roll-pitch-yaw (in radians) to 6D rotation representation.
    
    Args:
        rpy: array-like (..., 3)
    Returns:
        rot6d: array (..., 6)
    """
    r = R.from_euler("xyz", rpy)
    rot_mats = r.as_matrix()               # (..., 3, 3)
    # Take first two columns and flatten
    rot6d = rot_mats[..., :3, :2].reshape(*rpy.shape[:-1], 6)
    return rot6d

def decode_angles(rot6d):
    """
    Decode 6D rotation representation back to roll-pitch-yaw (xyz order).
    
    Args:
        rot6d: array (..., 6)
    Returns:
        rpy: array (..., 3)
    """
    # Reshape to (..., 3, 2)
    a1 = rot6d[..., [0, 2, 4]]
    a2 = rot6d[..., [1, 3, 5]]
    print(f"a1 : {a1}", flush=True)
    print(f"a2 : {a2}", flush=True)

    # Gram-Schmidt orthogonalization with strict normalization
    b1 = a1 / np.linalg.norm(a1, axis=-1, keepdims=True)
    a2 = a2 - np.sum(b1 * a2, axis=-1, keepdims=True) * b1
    b2 = a2 / np.linalg.norm(a2, axis=-1, keepdims=True)
    b3 = np.cross(b1, b2, axis=-1)
    b3 = b3 / np.linalg.norm(b3, axis=-1, keepdims=True)

    # Stack columns to form rotation matrix
    rot_mats = np.stack([b1, b2, b3], axis=-1)  # (..., 3, 3)
    print(rot_mats, flush=True)
    # Convert back to RPY
    r = R.from_matrix(rot_mats)
    rpy = r.as_euler("xyz", degrees=False)
    return rpy

@dataclass
class ObjectState:
    name: str = "None"
    position: List[List[float]] = field(
        default_factory=lambda: [
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
        ]
    )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "position": self.position,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ObjectState":
        return cls(
            name=data.get("name", "None"),
            position=data.get("position", [[0.0, 0.0, 0.0]] * 3),
        )

    def __repr__(self) -> str:
        return f"ObjectState(name={self.name}, position={self.position})"


@dataclass
class RobotData:
    action: str = "idle"
    objects: List[ObjectState] = field(default_factory=list)
    eef_position: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    joint_positions: List[float] = field(default_factory=lambda: [0.0] * 6)
    finger_positions: List[float] = field(default_factory=lambda: [0.0] * 17)
    
    def add_object(self, name: str, position: List[List[float]] = None):
        if position is None:
            position = [[0.0, 0.0, 0.0]] * 3
        self.objects.append(ObjectState(name=name, position=position))
    
    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "objects": [obj.to_dict() for obj in self.objects],
            "eef_position": self.eef_position,
            "joint_positions": self.joint_positions,
            "finger_positions": self.finger_positions,
        }

    def to_model_input(self) -> dict:
        """
        Convert the state to a format suitable for the model input.
        """
        obj_names = [obj.name for obj in self.objects]
        obj_positions = [
            [[float("inf"), float("inf"), float("inf")] if point[0] < -0.8 else point for point in obj.position] for obj in self.objects
        ]
        obj_positions_tensor = torch.tensor(obj_positions, dtype=torch.float32)
        eef_position = torch.tensor(self.eef_position[:3], dtype=torch.float32)
        eef_orientation = torch.tensor((encode_angles(np.array(self.eef_position[3:]))), dtype=torch.float32)
        # wrist_position = torch.tensor([self.finger_positions[-1]], dtype=torch.float32)
        # finger_synergy = pca2.transform(np.array(self.finger_positions[:-1]).reshape(1, -1))
        # finger_synergy_tensor = torch.tensor(finger_synergy, dtype=torch.float32).squeeze(0)
        finger_positions = torch.tensor([x * DEG_TO_RAD for x in self.finger_positions[:-1]], dtype=torch.float32)

        return {
            'action': self.action,
            'objects': obj_names,
            'obj_positions': obj_positions_tensor,
            'eef_position': eef_position,
            'eef_orientation': eef_orientation,
            # 'wrist_position': wrist_position,
            'finger_positions': finger_positions,
        }
    
    def to_model_output(self) -> dict:
        """
        Convert the model output to a format suitable for the environment.
        """
        eef_position = torch.tensor(self.eef_position[:3], dtype=torch.float32)
        eef_orientation = torch.tensor((encode_angles(np.array(self.eef_position[3:]))), dtype=torch.float32)
        wrist_position = torch.tensor([self.finger_positions[-1]], dtype=torch.float32)
        finger_positions = torch.tensor([x * DEG_TO_RAD for x in self.finger_positions[:-1]], dtype=torch.float32)

        delta = eef_position - torch.zeros(3, dtype=torch.float32)
        if len(self.objects) > 0:
            obj_mid_point = self.objects[0].position[4]
            obj_mid_point_tensor = torch.tensor(obj_mid_point, dtype=torch.float32)
            delta = eef_position - obj_mid_point_tensor

        return torch.cat(
            (delta, eef_orientation, finger_positions),
            # (delta, eef_orientation),
            dim=0
        )

    @classmethod
    def from_dict(cls, data: dict) -> "RobotData":
        print(f'data: {data}')
        return cls(
            action=data.get("action", "idle"),
            objects=[ObjectState.from_dict(obj) for obj in data.get("objects", [])],
            eef_position=data.get("eef_position", [0.0, 0.0, 0.0]),
            joint_positions=data.get("joint_positions", [0.0] * 6),
            finger_positions=data.get("finger_positions", [0.0] * 17),
        )

    def __repr__(self) -> str:
        return (
            f"RobotData(action={self.action}, "
            f"objects={self.objects}, "
            f"eef_position={self.eef_position}, "
            f"joint_positions={self.joint_positions}, "
            f"finger_positions={self.finger_positions})"
        )
