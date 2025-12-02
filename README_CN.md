# AI 机器人手部控制系统 (04bot_Hand)

## 项目简介

这是一个基于 ROS2 的智能机器人系统，结合了**语音识别**、**视觉感知**和**机器人控制**技术，能够通过自然语言命令控制机械臂和灵巧手执行复杂的抓取和操作任务。

## 核心功能

### 1. 🎤 语音控制
- **语音识别**：使用 Groq Whisper API 将语音转换为文字
- **自然语言理解**：使用 LLM (Llama) 解析语音命令，将高层指令（如"倒一杯水"）自动拆解为机器人可执行的动作序列
- **实时交互**：支持键盘触发（Ctrl+X）开始语音输入

### 2. 👁️ 视觉感知
- **物体检测**：基于 YOLO-World 模型进行实时物体检测
- **深度感知**：结合 RGB-D 相机（Astra Pro）获取物体的 3D 位置
- **动态词汇表**：根据语音命令动态更新检测目标
- **坐标转换**：将检测到的物体坐标转换到世界坐标系

### 3. 🤖 机器人控制
- **机械臂控制**：支持 Aubo 和 Jaka 机械臂
- **灵巧手控制**：支持 Orca 灵巧手
- **策略网络**：基于深度学习的控制策略
- **动作执行**：自动执行抓取（grasp）、倾倒（pour）、放置（place）等动作

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                     用户交互层                            │
│  - 语音输入 (Ctrl+X 触发)                                │
│  - 可视化显示 (YOLO检测结果, RViz)                       │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│              自然语言处理层                               │
│  - Groq Whisper (语音转文字)                             │
│  - Llama LLM (命令解析)                                  │
│  - 动作序列生成                                          │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                视觉感知层                                 │
│  - YOLO-World (物体检测)                                 │
│  - Astra Pro 相机 (RGB-D)                                │
│  - TF2 (坐标变换)                                        │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│               机器人控制层                                │
│  - Policy Controller (策略网络)                          │
│  - Arm Controller (机械臂)                               │
│  - Hand Controller (灵巧手)                              │
└─────────────────────────────────────────────────────────┘
```

## 主要组件

### 1. ai_robotics_bringup
系统启动包，包含主要的 launch 文件：
- `bringup.launch.py`：启动完整系统（相机、语音、检测）
- `aubo_controller.launch.py`：启动 Aubo 机械臂控制器
- `jaka_controller.launch.py`：启动 Jaka 机械臂控制器

### 2. natural_language_commander
自然语言命令处理包，包含两个核心节点：

#### voice_to_command 节点
- 功能：语音识别和命令解析
- 订阅话题：
  - `/astra/color/image_raw`：相机图像
- 发布话题：
  - `/voice_commands`：解析后的命令序列
  - `/objects`：检测到的物体列表
- 快捷键：
  - `Ctrl+X`：开始语音录制
  - `Ctrl+Q`：停止录制
  - `Ctrl+Z`：退出程序
  - `Ctrl+M`：切换模式

#### open_yolo_detector 节点
- 功能：物体检测和 3D 定位
- 订阅话题：
  - `/astra/color/image_raw`：RGB 图像
  - `/astra/depth/image_raw`：深度图像
  - `/astra/color/camera_info`：相机参数
  - `/objects`：待检测物体列表
- 发布话题：
  - `/objects_details`：物体的 3D 位置信息
  - `/objects_points`：可视化标记

### 3. hand_controller
手部控制策略包：
- `policy_controller.py`：基于深度学习的控制策略
- `basic_grasping_policy.py`：基础抓取策略
- `number_gesture.py`：数字手势识别

### 4. drivers
硬件驱动包：
- **orbbec_camera**：Astra 系列相机驱动
- **aubo_ros2**：Aubo 机械臂驱动
- **jaka_ros2**：Jaka 机械臂驱动

### 5. orca_hand_hardware_interface
Orca 灵巧手硬件接口

## 环境要求

### 硬件
- **相机**：Astra Pro / Astra Pro 2（RGB-D 相机）
- **机械臂**：Aubo 或 Jaka 系列
- **灵巧手**：Orca Hand
- **麦克风**：用于语音输入
- **GPU**：NVIDIA GPU（用于 YOLO 推理）

### 软件
- **操作系统**：Ubuntu 22.04 或更高版本
- **ROS2**：Jazzy
- **Python**：3.12
- **CUDA**：用于 GPU 加速

### Python 依赖
```bash
pip install groq sounddevice soundfile numpy opencv-python ultralytics torch pynput
```

## 安装与配置

### 1. 克隆项目
```bash
git clone <repository_url>
cd 04bot_Hand
```

### 2. 安装 ROS2 依赖
```bash
sudo apt update
sudo apt install ros-jazzy-desktop-full
```

### 3. 配置 Python 虚拟环境
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # 如果有的话
```

### 4. 配置 Groq API 密钥

**方法 1：环境变量（推荐）**
```bash
# 编辑 ~/.bashrc
nano ~/.bashrc

# 添加以下行（替换为你的真实密钥）
export GROQ_API_KEY='gsk_xxxxxxxxxxxxxxxxxxxxxxxx'

# 重新加载配置
source ~/.bashrc
```

**方法 2：临时设置**
```bash
export GROQ_API_KEY='gsk_xxxxxxxxxxxxxxxxxxxxxxxx'
```

**验证密钥设置**
```bash
echo $GROQ_API_KEY
# 或运行测试脚本
python3 test_groq_key.py
```

### 5. 下载 YOLO 模型
```bash
# 下载 YOLO-World 模型
cd ~/AI_hand
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8l-worldv2.pt
```

### 6. 配置相机权限
```bash
# 复制 udev 规则
sudo cp SUBSYSTEM=usb,ATTR{idVendor}=2bc5,MODE=0666,GROUP=plugdev /etc/udev/rules.d/99-orbbec.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### 7. 编译项目
```bash
# 在项目根目录
colcon build --symlink-install
source install/setup.bash
```

## 使用说明

### 启动完整系统

```bash
# 1. 进入项目目录
cd ~/AI_hand

# 2. 激活虚拟环境
source .venv/bin/activate

# 3. 加载环境变量
source ~/.bashrc

# 4. Source ROS2 工作空间
source install/setup.bash

# 5. 启动系统
ros2 launch ai_robotics_bringup bringup.launch.py
```

### 系统启动后你会看到：

1. **相机节点**启动，输出相机连接信息
2. **YOLO 检测器**加载模型
3. **语音命令节点**等待输入

### 使用语音控制

1. **按下 `Ctrl+X`** 开始语音录制
2. **说出你的命令**，例如：
   - "把水壶拿起来"
   - "倒一杯水"
   - "把杯子放到桌子上"
3. 系统会：
   - 将语音转换为文字
   - 识别图像中的物体
   - 解析命令并生成动作序列
   - 控制机器人执行动作

### 支持的动作类型

系统支持以下基本动作（可在 `voice_to_command.py` 的 `SYSTEM_PROMT` 中查看）：

- `grasp`：抓取物体
- `pick`：拾取物体
- `pour`：倾倒（如倒水）
- `drop`：放下物体
- `place`：放置物体到指定位置

### 命令示例

| 语音命令 | 生成的动作序列 |
|---------|--------------|
| "拿起水壶" | `[{"action": "grasp", "target_name": "kettle"}]` |
| "倒水到杯子里" | `[{"action": "grasp", "target_name": "kettle"}, {"action": "pour", "target_name": "cup"}]` |
| "把书放到桌子上" | `[{"action": "grasp", "target_name": "book"}, {"action": "place", "target_name": "table"}]` |

### 可视化

系统提供以下可视化：
- **YOLO 检测窗口**：显示实时物体检测结果
- **RViz**（可选）：显示 3D 点云和坐标系

```bash
# 在另一个终端启动 RViz
rviz2
```

## 常见问题

### 1. Groq API 认证失败（401 错误）

**问题**：
```
groq.AuthenticationError: Error code: 401 - {'error': {'message': 'Invalid API Key'}}
```

**解决方法**：
```bash
# 检查密钥是否设置
echo $GROQ_API_KEY

# 如果为空，重新设置
nano ~/.bashrc
# 添加: export GROQ_API_KEY='你的密钥'
source ~/.bashrc

# 在虚拟环境中重新加载
cd ~/AI_hand
source .venv/bin/activate
source ~/.bashrc

# 测试密钥
python3 test_groq_key.py
```

### 2. 相机连接失败

**检查相机是否连接**：
```bash
lsusb | grep 2bc5
```

**检查相机权限**：
```bash
ls -l /dev/bus/usb/
```

### 3. CUDA/GPU 相关错误

如果没有 NVIDIA GPU，修改 `open_yolo_detector.py` 第 41 行：
```python
# 从
self.model.to("cuda")
# 改为
self.model.to("cpu")
```

### 4. 音频设备问题

**列出可用音频设备**：
```bash
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```

## 项目结构

```
04bot_Hand/
├── src/
│   ├── ai_robotics_bringup/       # 系统启动包
│   │   ├── launch/                # Launch 文件
│   │   └── scripts/               # 测试脚本
│   ├── natural_language_commander/ # 自然语言处理
│   │   ├── voice_to_command.py    # 语音识别节点
│   │   └── open_yolo_detector.py  # 物体检测节点
│   ├── hand_controller/           # 手部控制策略
│   │   ├── policy_controller.py
│   │   └── basic_grasping_policy.py
│   ├── hand_control_msgs/         # 消息定义
│   ├── drivers/                   # 硬件驱动
│   │   ├── astra_camera/          # 相机驱动
│   │   ├── aubo_ros2/             # Aubo 机械臂
│   │   └── jaka_ros2/             # Jaka 机械臂
│   └── orca_hand_hardware_interface/ # 灵巧手接口
├── models/                        # 模型文件
├── test_groq_key.py              # API 密钥测试脚本
└── README_CN.md                  # 本文档
```

## 技术栈

- **ROS2 Jazzy**：机器人操作系统
- **Groq API**：
  - Whisper Large V3 Turbo：语音识别
  - Llama 4 Maverick：自然语言理解
- **YOLO-World**：开放词汇物体检测
- **PyTorch**：深度学习框架
- **OpenCV**：计算机视觉
- **TF2**：坐标变换

## 开发团队

维护者：Hoang Dung Dinh (dinhhoangdung0712@gmail.com)

## 许可证

待定（见 package.xml）

## 更新日志

- **2025-12-02**：添加 Groq API 密钥诊断脚本
- 支持语音控制和物体检测的完整流程

## 参考资料

- [ROS2 文档](https://docs.ros.org/en/jazzy/)
- [Groq API 文档](https://console.groq.com/docs)
- [YOLO-World 项目](https://github.com/ultralytics/ultralytics)
- [Astra 相机驱动](https://github.com/orbbec/OrbbecSDK_ROS2)

---

如有问题，请参考"常见问题"部分或联系维护者。
