import queue
import threading
import cv2
from enhancer import Enhancer

from tensorflow import keras
import time
from stream import Streamer

output_dir = 'frames'
q = queue.Queue()

# model = keras.models.load_model('models/generator.h5')
# inputs = keras.Input((None, None, 3))
# output = model(inputs)
# model = keras.models.Model(inputs, output)

stream_addr = 'rtmp://192.168.1.7/live/test'
while True:
    cap = cv2.VideoCapture(stream_addr)
    if cap.isOpened():
        break
    else:
        time.sleep(0.3)
width = 1280
height = 720
fps = 30.

stream = Streamer(height, width, fps)
enhancer = Enhancer()


def background():
    while True:
        ret, frame = cap.read()
        if frame is not None:
            # im_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            q.put(frame)
    cap.release()


def foreground():
    while True:
        print(q.qsize())
        frame = q.get()
        # frame = frame / 255.0
        print(stream.get_video_frame_buffer_state())
        if stream.get_video_frame_buffer_state() < fps:
            sr = enhancer.enhance(frame)
            stream.send_video_frame(sr, frame_counter=None)
        q.task_done()


b = threading.Thread(name='background', target=background)
f = threading.Thread(name='foreground', target=foreground)

f.start()

b.start()
