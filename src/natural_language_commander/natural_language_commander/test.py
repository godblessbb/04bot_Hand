# test_mic.py
import sounddevice as sd
import numpy as np

SAMPLE_RATE = 16000
BLOCK_SEC   = 0.1
THRESHOLD   = 10    # 极低的阈值

def callback(indata, frames, time_info, status):
    pcm = (np.clip(indata[:,0], -1,1)*32767).astype(np.int16).tobytes()
    rms = np.sqrt((np.frombuffer(pcm, dtype=np.int16).astype(np.float32)**2).mean())
    print(f"RMS={rms:.1f}")

with sd.InputStream(
    samplerate=SAMPLE_RATE,
    channels=1,
    blocksize=int(SAMPLE_RATE*BLOCK_SEC),
    callback=callback
):
    print("Recording... 说话试试，大约 5 秒后结束")
    sd.sleep(5000)