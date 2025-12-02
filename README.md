# AI Robot Hand Control System (04bot_Hand)

[中文文档](README_CN.md)

## Overview

An intelligent robot system based on ROS2 that combines **voice recognition**, **visual perception**, and **robot control** to execute complex grasping and manipulation tasks through natural language commands.

## Key Features

- 🎤 **Voice Control**: Groq Whisper API for speech-to-text, LLM for command parsing
- 👁️ **Visual Perception**: YOLO-World for object detection, RGB-D camera for 3D localization
- 🤖 **Robot Control**: Support for Aubo/Jaka arms and Orca dexterous hand

## Quick Start

### 1. Setup Groq API Key

```bash
echo 'export GROQ_API_KEY="gsk_your_key_here"' >> ~/.bashrc
source ~/.bashrc
```

### 2. Build and Launch

```bash
cd ~/AI_hand
source .venv/bin/activate
colcon build --symlink-install
source install/setup.bash
ros2 launch ai_robotics_bringup bringup.launch.py
```

### 3. Use Voice Control

- Press `Ctrl+X` to start voice recording
- Speak your command (e.g., "pick up the kettle")
- The system will detect objects and execute actions

## System Architecture

```
User Input (Voice) → NLP (Groq) → Vision (YOLO-World) → Robot Control
```

## Main Components

- **ai_robotics_bringup**: System launch files
- **natural_language_commander**: Voice and vision processing
- **hand_controller**: Control policies
- **drivers**: Hardware drivers (camera, arm)
- **orca_hand_hardware_interface**: Dexterous hand interface

## Requirements

- Ubuntu 22.04+
- ROS2 Jazzy
- Python 3.12
- NVIDIA GPU (optional, for YOLO)
- Astra Pro camera
- Groq API key

## Supported Actions

- `grasp`: Grasp object
- `pick`: Pick up object
- `pour`: Pour liquid
- `drop`: Drop object
- `place`: Place object at location

## Documentation

See [README_CN.md](README_CN.md) for detailed Chinese documentation.

## Troubleshooting

**API Key Error (401)**:
```bash
# Verify key is set
echo $GROQ_API_KEY
# Test key
python3 test_groq_key.py
```

**Camera Not Found**:
```bash
lsusb | grep 2bc5
```

## Maintainer

Hoang Dung Dinh (dinhhoangdung0712@gmail.com)

## License

TBD
