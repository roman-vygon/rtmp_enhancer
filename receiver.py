import queue
import threading
import cv2
from enhancer import Enhancer
import numpy as np
from tensorflow import keras
import time
from stream import Streamer

output_dir = 'frames'
q = queue.Queue()

q_out = queue.Queue()
# model = keras.models.load_model('models/generator.h5')
# inputs = keras.Input((None, None, 3))
# output = model(inputs)
# model = keras.models.Model(inputs, output)

stream_addr = 'videoplayback.mp4'  # rtmp://192.168.1.7/live/test'
while True:
    cap = cv2.VideoCapture(stream_addr)
    if cap.isOpened():
        break
    else:
        time.sleep(0.3)
width = 640*3
height = 360*3
fps = 30.

stream = Streamer(height, width, fps)
enhancer = Enhancer()


def read():
    while True:
        ret, frame = cap.read()
        if frame is not None:
            im_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            q.put(im_rgb)
            #print(im_rgb.tostring())
    cap.release()


def enhance():
    while True:
        print("Q: %d" % q.qsize())
        if q.qsize() > 0:
            frame = q.get()
            sr = enhancer.enhance(frame)
            q_out.put(sr)
            q.task_done()


def send():
    i = 0
    while True:
        print("Q_OUT: %d" % q_out.qsize())
        if True:#stream.get_video_frame_buffer_state() < fps and q_out.qsize() > 0:
            frame = q_out.get()
            stream.send_video_frame(frame, frame_counter=None)
            i += 1
            q_out.task_done()


r = threading.Thread(name='read', target=read)
e = threading.Thread(name='enhance', target=enhance)
s = threading.Thread(name='send', target=send)

r.start()
e.start()
s.start()
