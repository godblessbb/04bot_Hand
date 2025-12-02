      
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import io
import queue
from collections import deque
import time
import json
import threading
import numpy as np
import sounddevice as sd
import soundfile as sf
from pynput import keyboard as kb
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from std_msgs.msg import String
import sensor_msgs.msg
from cv_bridge import CvBridge
import cv2
import base64
from groq import Groq

"""
For actions
"""
SYSTEM_PROMT = (
    "你是一个指令解析助手。接收到用户一条操作指令，需要完成以下流程：\n"
    "1. **理解用户指令的高层意图**（如“倒一杯水”），并基于步骤1中的环境要素，自动拆解出完整的子动作序列：\n"
    "   - 每个子动作必须包含：\n"
    "     • action：英文动词，必须从 [“grasp”, “pick”, “pour”, “drop”, “place”] 中选择。\n"
    "     • target_name：对应物体的名称（与步骤1一致）。\n"
    "   - 动作序列要覆盖所有位移和状态变化（例如：拿起、移动到指定位置、倾倒、放下等），并按执行顺序排列。\n"
    "3. **处理指令中提及但在图片中未检测到的对象**：\n"
    "   - 对于每个此类对象，输出：\n"
    "     {\"action\": \"none\", \"target_name\": \"none\"}\n"
    "4. **严格输出**：\n"
    "   - 最终结果为一个 JSON 数组，元素按动作执行的先后顺序排列。\n"
    "   - 即使只有一个动作，也必须使用数组形式。\n"
    "   - 不要输出任何额外文字。\n"
    "\n"
    "**示例最终输出**：\n"
    "[\n"
    "  {\"action\": \"grasp\",  \"target_name\": \"kettle\", \n"
    "  {\"action\": \"pour\",  \"target_name\": \"cup\",\n"
    "  {\"action\": \"place\", \"target_name\": \"kettle\",   \n"
    "]"
)

"""
For number gestures
"""
# SYSTEM_PROMT = """你是一个语音命令解析器。用户会说出数字或动作指令，你需要将其转换为对应的数字指令。映射规则：如果用户只提到了某个0-10之间的整数，直接返回该整数，如果用户提到了某些计算要求且结果位于0-10之间，把计算结果返回。不要任何解释。"""


class VoiceToCommand(Node):
    def __init__(self):
        super().__init__('voice_to_command')

        # ========== ROS2 Interface ==========
        self.command_publisher = self.create_publisher(String, 'voice_commands', 10)
        self.objects_publisher = self.create_publisher(String, 'objects', 10)
        self.image_subscriber = self.create_subscription(
            sensor_msgs.msg.Image,
            'astra/color/image_raw',
            self.image_callback,
            10
        )
        self.img_msg = None

        # ========== Config ==========
        self.GROQ_API_KEY   = os.environ.get("GROQ_API_KEY")
        self.ASR_MODEL      = "whisper-large-v3-turbo"
        self.LLM_MODEL      = "meta-llama/llama-4-maverick-17b-128e-instruct"
        self.SAMPLE_RATE    = 16000
        self.BLOCK_SEC      = 0.05  # 减少块大小，提高响应性
        self.SILENCE_TH     = 30    # 降低静音阈值
        self.SILENCE_GAP    = 2.0   # 增加静音间隔
        self.MIN_SPEECH_LEN = 0.3   # 最短语音长度

        # ========== State ==========
        self.groq_client = Groq(api_key=self.GROQ_API_KEY)
        self.audio_q = queue.Queue(maxsize=200)  # 限制队列大小
        self.audio_stats = {
            'blocks_received': 0,
            'blocks_processed': 0,
            'segments_saved': 0,
            'queue_overflows': 0
        }
        self.stop_flag = False
        self.recording_flag = False
        self.keyboard_mode = True
        # 使用双缓冲区
        self.current_segment = deque()
        self.backup_segment = deque()
        
        # 音频质量监控
        self.rms_history = deque(maxlen=50)
        self.last_audio_time = time.time()

        # Events
        self.start_event = threading.Event()
        self.stop_event = threading.Event()
        self.exit_event = threading.Event()
        self.switch_mode_event = threading.Event()

        # Start hotkey listener
        self.listener = kb.GlobalHotKeys({
            '<ctrl>+x': lambda: self.start_event.set(),
            '<ctrl>+q': lambda: self.stop_event.set(),
            '<ctrl>+z': lambda: self.exit_event.set(),
            '<ctrl>+m': lambda: self.switch_mode_event.set()
        })
        self.listener.start()

        # Launch voice processing thread
        self.voice_thread = threading.Thread(target=self.main_loop, daemon=True)

    def _cvt_ros_image_to_b64(self, ros_image):
        cv_image = CvBridge().imgmsg_to_cv2(ros_image, desired_encoding='bgr8')
        _, buffer = cv2.imencode('.jpg', cv_image)
        return base64.b64encode(buffer).decode('utf-8')
    
    def image_callback(self, msg):
        if self.recording_flag:
            return
        self.img_msg = msg


    def audio_callback(self, indata, frames, time_info, status):
        """改进的音频回调，添加详细监控"""
        if self.stop_flag:
            raise sd.CallbackStop()
            
        # 检查音频流状态
        if status:
            self.get_logger().warning(f"Audio callback status: {status}")
            
        # 记录接收时间
        current_time = time.time()
        self.last_audio_time = current_time
        
        # 转换音频数据
        pcm16 = (np.clip(indata[:, 0], -1, 1) * 32767).astype(np.int16)
        audio_block = pcm16.tobytes()
        
        # 计算RMS并记录
        rms_val = self.rms(audio_block)
        self.rms_history.append((current_time, rms_val))
        
        # 非阻塞队列操作
        try:
            self.audio_q.put_nowait((current_time, audio_block))
            self.audio_stats['blocks_received'] += 1
        except queue.Full:
            # 队列满时丢弃最老的数据
            try:
                self.audio_q.get_nowait()
                self.audio_q.put_nowait((current_time, audio_block))
                self.audio_stats['queue_overflows'] += 1
                self.get_logger().warning(f"Audio queue overflow,ped block")
            except queue.Empty:
                pass

    def rms(self, buf_bytes):
        """改进的RMS计算，添加异常处理"""
        try:
            arr = np.frombuffer(buf_bytes, dtype=np.int16).astype(np.float32)
            if len(arr) == 0:
                return 0.0
            return np.sqrt((arr**2).mean())
        except Exception as e:
            self.get_logger().error(f"RMS calculation error: {e}")
            return 0.0

    def detect_speech_boundaries(self, rms_history, current_time):
        """改进的语音边界检测"""
        if len(rms_history) < 5:
            return False, False
        
        recent_rms = [rms for _, rms in list(rms_history)[-10:]]
        avg_rms = np.mean(recent_rms)
        max_rms = np.max(recent_rms)
        self.get_logger().info(f"recent_rms:    {recent_rms}")
        # 动态阈值调整
        dynamic_threshold = max(self.SILENCE_TH, avg_rms * 0.3)
        
        is_speech = max_rms > dynamic_threshold
        
        # 检查语音结束
        silence_blocks = 0
        for timestamp, rms in reversed(rms_history):
            if current_time - timestamp > self.SILENCE_GAP:
                break
            if rms <= dynamic_threshold:
                silence_blocks += 1
            else:
                break
                
        speech_ended = silence_blocks > (self.SILENCE_GAP / self.BLOCK_SEC * 0.8)
        
        return is_speech, speech_ended

    def process_segment_improved(self, segment_blocks):
        """改进的音频段处理"""
        if not segment_blocks:
            self.get_logger().warning("Empty segment blocks")
            return
            
        self.get_logger().info(f"Processing segment with {len(segment_blocks)} blocks")
        
        # 提取音频数据
        audio_data = []
        start_time = segment_blocks[0][0]
        end_time = segment_blocks[-1][0]
        
        for timestamp, block in segment_blocks:
            audio_data.append(block)
        
        # 生成音频文件
        bio = self.flush_segment_improved(audio_data, start_time, end_time)
        if bio:
            text = self.transcribe_wav(bio)
            self.get_logger().info(f"Transcribed text: '{text}'")
            if text.strip():
                commands = self.parse_command_with_groq(text)
                if commands:
                    msg = String()
                    msg.data = json.dumps(commands, ensure_ascii=False)
                    self.command_publisher.publish(msg)
                    self.get_logger().info(f"Published commands: {commands}")

    def flush_segment_improved(self, buffers, start_time, end_time):
        """改进的音频段保存"""
        if not buffers:
            self.get_logger().warning("No audio buffers to flush")
            return None
            
        try:
            # 合并音频数据
            pcm = b"".join(buffers)
            audio_array = np.frombuffer(pcm, dtype=np.int16)
            
            if len(audio_array) == 0:
                self.get_logger().warning("Empty audio array")
                return None
            
            # 音频质量检查
            duration = len(audio_array) / self.SAMPLE_RATE
            avg_amplitude = np.mean(np.abs(audio_array))
            max_amplitude = np.max(np.abs(audio_array))
            
            self.get_logger().info(f"Audio segment: duration={duration:.2f}s, "
                       f"avg_amp={avg_amplitude:.1f}, max_amp={max_amplitude}")
            
            # 如果音频太小，可能是噪音
            if max_amplitude < 100:
                self.get_logger().warning("Audio amplitude too low, might be noise")
                return None
            
            # 保存到文件（带时间戳）
            timestamp_str = time.strftime("%Y%m%d_%H%M%S", time.localtime(start_time))
            filename = f"/home/brad/voice/output_{timestamp_str}.wav"
            sf.write(filename, audio_array, self.SAMPLE_RATE, format="WAV", subtype="PCM_16")
            self.get_logger().info(f"Saved audio to: {filename}")
            
            # 保存到内存
            bio = io.BytesIO()
            sf.write(bio, audio_array, self.SAMPLE_RATE, format="WAV", subtype="PCM_16")
            bio.seek(0)
            
            return bio
            
        except Exception as e:
            self.get_logger().error(f"Error in flush_segment_improved: {e}")
            return None

    def transcribe_wav(self, bio):
        """Send BytesIO audio directly to Groq API."""
        resp = self.groq_client.audio.transcriptions.create(
            file=("audio.wav", bio, "audio/wav"),
            model=self.ASR_MODEL,
            language='zh'
        )
        return (resp.text or "").strip()

    def parse_command_with_groq(self, command):
        if self.img_msg is None:
            self.get_logger().warning("No image available for command parsing.")
            return []
        img_b64 = self._cvt_ros_image_to_b64(self.img_msg)
        try:
            # Ask the LLM to find all objects
            user_prompt = [
                {
                    "type": "text", 
                    "text": """List all objects in this image without any description (use singular nouns). 
                                You must return only a Python-like list of strings, no other description, output is string. 
                                For example: ["kettle", "cup", "bottle"]."""},

                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_b64}",
                    },
                },
            ]
            resp = self.groq_client.chat.completions.create(
                model=self.LLM_MODEL,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=0.0,
            )
            content = resp.choices[0].message.content.strip()
            self.objects_publisher.publish(String(data=content))
            object_stamp = self.get_clock().now().seconds_nanoseconds()[0]

            user_prompt = f"Parse command: {command}, objects: {content}"
            self.get_logger().info(f'User_prompt: {user_prompt}')
            resp = self.groq_client.chat.completions.create(
                model=self.LLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,
                max_tokens=300
            )
            content = resp.choices[0].message.content.strip()
            self.get_logger().info(f'Response: {content}')

            while self.get_clock().now().seconds_nanoseconds()[0] - object_stamp < 2.0:
                time.sleep(0.5)

            return content
        except Exception as e:
            self.get_logger().error(f"Parse error: {e}")
            return []

    def print_audio_stats(self):
        """打印音频处理统计"""
        stats = self.audio_stats
        queue_size = self.audio_q.qsize()
        rms_recent = [rms for _, rms in list(self.rms_history)[-10:]]
        avg_rms = np.mean(rms_recent) if rms_recent else 0
        
        self.get_logger().info(f"Audio Stats - Received: {stats['blocks_received']}, "
                   f"Processed: {stats['blocks_processed']}, "
                   f"Segments: {stats['segments_saved']}, "
                   f"Overflows: {stats['queue_overflows']}, "
                   f"Queue: {queue_size}, Avg RMS: {avg_rms:.1f}")

    def start_stream(self):
        """改进的音频流启动"""
        try:
            stream = sd.InputStream(
                samplerate=self.SAMPLE_RATE,
                channels=1,
                dtype="float32",
                blocksize=int(self.SAMPLE_RATE * self.BLOCK_SEC),
                callback=self.audio_callback,
                latency='low'  # 降低延迟
            )
            stream.start()
            self.get_logger().info(f"Audio stream started: {self.SAMPLE_RATE}Hz, "
                       f"block_size={int(self.SAMPLE_RATE * self.BLOCK_SEC)}")
            return stream
        except Exception as e:
            self.get_logger().error(f"Failed to start audio stream: {e}")
            raise

    def wait_for_start_signal(self):
        mode_text = "Keyboard Mode" if self.keyboard_mode else "Voice Mode"
        self.get_logger().info(f"Waiting in {mode_text}...")

        if self.keyboard_mode:
            while rclpy.ok():
                if self.exit_event.is_set():
                    self.get_logger().info("Exit signal detected.")
                    rclpy.shutdown()
                    return False
                if self.switch_mode_event.is_set():
                    self.switch_mode_event.clear()
                    self.keyboard_mode = False
                    self.get_logger().info("Switched to Voice Mode.")
                    return False
                if self.start_event.is_set():
                    self.start_event.clear()
                    self.get_logger().info("Detected Ctrl+X, start listening.")
                    return True
                time.sleep(0.1)
        # else:
        #     stream = self.start_stream()
        #     seg_buf, last_voice = [], 0.0
        #     try:
        #         while rclpy.ok():
        #             if self.exit_event.is_set():
        #                 rclpy.shutdown()
        #                 return False
        #             if self.switch_mode_event.is_set():
        #                 self.switch_mode_event.clear()
        #                 self.keyboard_mode = True
        #                 return False
        #             try:
        #                 block = self.audio_q.get(timeout=0.1)
        #             except queue.Empty:
        #                 if seg_buf and time.time() - last_voice > self.SILENCE_GAP:
        #                     bio = self.flush_segment(seg_buf)
        #                     seg_buf = []
        #                     if bio:
        #                         text = self.transcribe_wav(bio)
        #                         if "hello" in text.lower() or "你好" in text:
        #                             return True
        #                 continue
        #             if self.rms(block) > self.SILENCE_TH:
        #                 last_voice = time.time()
                    
        #             seg_buf.append(block)
        #     finally:
        #         self.stop_flag = True
        #         stream.stop()
        #         stream.close()
        #         self.stop_flag = False

    def listening_loop(self):
        """改进的监听循环，添加详细状态跟踪"""
        self.get_logger().info(f"Starting improved listening loop")
        self.recording_flag = True
        
        stream = self.start_stream()
        speech_start_time = None
        last_speech_time = None
        segment_blocks = []
        
        # 统计信息
        loop_count = 0
        
        try:
            while rclpy.ok():
                loop_count += 1
                current_time = time.time()
                
                # 检查退出条件
                if self.keyboard_mode:
                    if self.exit_event.is_set():
                        rclpy.shutdown()
                        return
                    if self.stop_event.is_set():
                        self.stop_event.clear()
                        if segment_blocks:
                            self.process_segment_improved(segment_blocks)
                            segment_blocks = []
                        return
                
                # 获取音频数据
                try:
                    timestamp, block = self.audio_q.get(timeout=0.05)  # 减少超时
                    self.audio_stats['blocks_processed'] += 1
                except queue.Empty:
                    # 检查是否长时间没有音频数据
                    if current_time - self.last_audio_time > 1.0:
                        self.get_logger().warning("No audio data received for 1 second")
                    
                    # 检查是否需要处理当前段
                    if segment_blocks and last_speech_time:
                        if current_time - last_speech_time > self.SILENCE_GAP:
                            self.process_segment_improved(segment_blocks)
                            segment_blocks = []
                            speech_start_time = None
                            last_speech_time = None
                    continue
                
                # 语音活动检测
                rms_val = self.rms(block)
                is_speech, speech_ended = self.detect_speech_boundaries(
                    self.rms_history, current_time
                )
                
                # 记录语音活动
                if is_speech:
                    if speech_start_time is None:
                        speech_start_time = current_time
                        self.get_logger().info(f"Speech started at {current_time}")
                    last_speech_time = current_time
                
                # 添加到当前段
                segment_blocks.append((timestamp, block))
                
                # 检查是否需要处理段
                if speech_ended and segment_blocks:
                    speech_duration = last_speech_time - speech_start_time if speech_start_time else 0
                    if speech_duration >= self.MIN_SPEECH_LEN:
                        self.get_logger().info(f"Processing speech segment: duration={speech_duration:.2f}s, blocks={len(segment_blocks)}")
                        self.process_segment_improved(segment_blocks)
                        self.audio_stats['segments_saved'] += 1
                    else:
                        self.get_logger().info(f"Discarding short speech segment: duration={speech_duration:.2f}s")
                    
                    segment_blocks = []
                    speech_start_time = None
                    last_speech_time = None
                
                # 防止段过长
                if len(segment_blocks) > 1000:  # 约50秒
                    self.get_logger().warning("Segment too long, force processing")
                    self.process_segment_improved(segment_blocks)
                    segment_blocks = []
                    speech_start_time = None
                    last_speech_time = None
                
                # 定期输出统计信息
                if loop_count % 1000 == 0:
                    self.print_audio_stats()
                    
        except Exception as e:
            self.get_logger().error(f"Error in listening loop: {e}")
        finally:
            # 处理剩余的音频段
            if segment_blocks:
                self.get_logger().info("Processing remaining audio segment")
                self.process_segment_improved(segment_blocks)
                segment_blocks = []
                
            self.stop_flag = True
            stream.stop()
            stream.close()
            self.stop_flag = False
            self.recording_flag = False
            self.print_audio_stats()

    def main_loop(self):
        self.get_logger().info("VoiceToCommand Node main loop started.")
        while rclpy.ok():
            if self.wait_for_start_signal():
                self.listening_loop()


def main(args=None):
    rclpy.init(args=args)
    node = VoiceToCommand()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    ros_thread = threading.Thread(target=executor.spin, daemon=True)
    ros_thread.start()
    node.voice_thread.start()
    try:
        while rclpy.ok():
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

    