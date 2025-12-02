# 快速入门指南

## 第一次使用？按照以下步骤操作

### 步骤 1：配置 Groq API 密钥 ⭐ 重要！

```bash
# 编辑配置文件
nano ~/.bashrc

# 在文件末尾添加（替换为你的真实密钥）
export GROQ_API_KEY='gsk_xxxxxxxxxxxxxxxxxxxxxxxx'

# 保存并退出（Ctrl+O, Enter, Ctrl+X）

# 重新加载配置
source ~/.bashrc

# 验证设置
echo $GROQ_API_KEY
```

**获取 Groq API 密钥**：
1. 访问：https://console.groq.com/keys
2. 注册/登录账号
3. 点击 "Create API Key"
4. 复制密钥（以 `gsk_` 开头）

### 步骤 2：下载 YOLO 模型

```bash
cd ~/AI_hand
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8l-worldv2.pt
```

### 步骤 3：编译项目

```bash
cd ~/AI_hand
colcon build --symlink-install
source install/setup.bash
```

### 步骤 4：测试 API 密钥

```bash
cd ~/AI_hand
source .venv/bin/activate
source ~/.bashrc
python3 test_groq_key.py
```

**预期输出**：
```
API Key 长度: 56
API Key 前缀: gsk_xxxxx
✓ API 密钥有效!
响应: API key works!
```

### 步骤 5：启动系统

```bash
cd ~/AI_hand
source .venv/bin/activate
source ~/.bashrc
source install/setup.bash
ros2 launch ai_robotics_bringup bringup.launch.py
```

### 步骤 6：使用语音控制

1. **按下 `Ctrl+X`** - 开始语音录制
2. **说出命令** - 例如："拿起水壶"
3. **按下 `Ctrl+Q`** - 停止录制（或自动检测语音结束）
4. **观察执行** - 查看 YOLO 检测窗口和机器人动作

## 常用命令

### 测试相机

```bash
ros2 launch orbbec_camera astra_pro2.launch.py
# 在另一个终端
ros2 run rqt_image_view rqt_image_view
```

### 查看话题

```bash
# 列出所有话题
ros2 topic list

# 查看语音命令
ros2 topic echo /voice_commands

# 查看检测到的物体
ros2 topic echo /objects_details
```

### 可视化

```bash
# 启动 RViz
rviz2
# 添加以下显示：
# - TF
# - Image (选择 /astra/color/image_raw)
# - Marker (选择 /objects_points)
```

## 快捷键

- `Ctrl+X`：开始语音录制
- `Ctrl+Q`：停止录制
- `Ctrl+Z`：退出程序
- `Ctrl+M`：切换模式（键盘/语音）
- `Ctrl+C`：终止 launch 文件

## 示例命令

### 中文命令
- "把水壶拿起来"
- "倒一杯水"
- "把杯子放到桌子上"
- "抓住剪刀"

### 命令格式
系统会将命令解析为动作序列，例如：
```json
[
  {"action": "grasp", "target_name": "kettle"},
  {"action": "pour", "target_name": "cup"},
  {"action": "place", "target_name": "kettle"}
]
```

## 故障排除

### 问题 1：API 密钥无效（401 错误）

```bash
# 1. 检查密钥
echo $GROQ_API_KEY

# 2. 如果为空，重新设置
nano ~/.bashrc
# 添加: export GROQ_API_KEY='你的密钥'

# 3. 重新加载
source ~/.bashrc

# 4. 在虚拟环境中重新加载（重要！）
cd ~/AI_hand
source .venv/bin/activate
source ~/.bashrc

# 5. 测试
python3 test_groq_key.py
```

### 问题 2：相机未找到

```bash
# 检查相机连接
lsusb | grep 2bc5

# 应该看到类似：
# Bus 001 Device 005: ID 2bc5:060f Orbbec Astra Pro Plus

# 如果没有，检查 USB 连接
```

### 问题 3：YOLO 模型未找到

```bash
# 检查模型文件
ls -lh ~/AI_hand/yolov8l-worldv2.pt

# 如果不存在，重新下载
cd ~/AI_hand
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8l-worldv2.pt
```

### 问题 4：音频设备错误

```bash
# 列出音频设备
python3 -c "import sounddevice as sd; print(sd.query_devices())"

# 测试麦克风
arecord -l
```

### 问题 5：GPU/CUDA 错误

如果没有 NVIDIA GPU，修改 `src/natural_language_commander/natural_language_commander/open_yolo_detector.py`：

```python
# 第 41 行，从：
self.model.to("cuda")
# 改为：
self.model.to("cpu")
```

## 检查清单

在启动系统前，确保：

- [ ] Groq API 密钥已设置（`echo $GROQ_API_KEY`）
- [ ] YOLO 模型已下载（`ls ~/AI_hand/yolov8l-worldv2.pt`）
- [ ] 相机已连接（`lsusb | grep 2bc5`）
- [ ] 虚拟环境已激活（`source .venv/bin/activate`）
- [ ] ROS2 工作空间已 source（`source install/setup.bash`）
- [ ] 麦克风已连接并测试

## 系统日志

日志文件位置：
```bash
~/.ros/log/
```

查看最新日志：
```bash
cd ~/.ros/log/
ls -lt | head
```

## 需要帮助？

1. 查看完整文档：[README_CN.md](README_CN.md)
2. 检查常见问题章节
3. 查看系统日志
4. 联系维护者

---

**祝你使用愉快！** 🚀
