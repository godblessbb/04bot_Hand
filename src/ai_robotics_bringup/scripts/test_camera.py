from openni import openni2
import numpy as np
import cv2
import time
import os

# Global depth data
dpt = None

def mousecallback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDBLCLK:
        print(y, x, dpt[y, x])


if __name__ == "__main__": 
    openni2.initialize()
    dev = openni2.Device.open_any()
    print(dev.get_device_info())

    depth_stream = dev.create_depth_stream()
    depth_stream.start()

    color_stream = dev.create_color_stream()
    color_stream.start()

    cv2.namedWindow('depth')
    cv2.setMouseCallback('depth', mousecallback)

    cv2.namedWindow('color')
    cv2.setMouseCallback('color', mousecallback)

    last_saved = time.time()
    save_interval = 2  # seconds

    while True:
        # Read and process depth frame
        frame = depth_stream.read_frame()
        dframe_data = np.array(frame.get_buffer_as_triplet()).reshape([480, 640, 2])
        dpt1 = np.asarray(dframe_data[:, :, 0], dtype='float32')
        dpt2 = np.asarray(dframe_data[:, :, 1], dtype='float32')
        
        dpt2 *= 255
        dpt = dpt1 + dpt2

        # Normalize depth for visualization
        dpt_display = cv2.convertScaleAbs(dpt, alpha=0.03)
        cv2.imshow('depth', dpt_display)

        # Read and process color frame
        cframe = color_stream.read_frame()
        cframe_data = np.array(cframe.get_buffer_as_triplet()).reshape([480, 640, 3])
        R = cframe_data[:, :, 0]
        G = cframe_data[:, :, 1]
        B = cframe_data[:, :, 2]
        color_img = np.transpose(np.array([B, G, R]), [1, 2, 0])
        cv2.imshow('color', color_img)

        # Save images every 2 seconds
        current_time = time.time()
        if current_time - last_saved >= save_interval:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            cv2.imwrite(f"depth_{timestamp}.png", dpt_display)
            cv2.imwrite(f"color_{timestamp}.png", color_img)
            print(f"Saved images at {timestamp}")
            last_saved = current_time

        key = cv2.waitKey(1)
        if int(key) == ord('q'):
            break

    depth_stream.stop()
    color_stream.stop()
    dev.close()