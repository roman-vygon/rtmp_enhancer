import os
import queue
import threading
import matplotlib.pyplot as plt
import cv2
import numpy as np
from tensorflow import keras
from twitchstream.outputvideo import TwitchBufferedOutputStream

from stream import Streamer

output_dir = 'frames'
q = queue.Queue()

model = keras.models.load_model('models/generator.h5')
inputs = keras.Input((None, None, 3))
output = model(inputs)
model = keras.models.Model(inputs, output)

stream_addr = 'rtmp://192.168.1.5/live/test'
cap = cv2.VideoCapture(stream_addr)

width = 128 * 4
height = 128 * 4
fps = 30.

stream = Streamer(height, width, fps)


def background():
    while True:
        ret, frame = cap.read()
        if frame is not None:
            #im_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            q.put(frame)
    cap.release()


def foreground():
    while True:
        frame = q.get()
        frame = frame / 255.0
        sr = model.predict(np.expand_dims(frame, axis=0))[0]

        sr = (sr + 1) / 2.

        #if stream.get_video_frame_buffer_state() < fps:
        stream.send_video_frame(sr, frame_counter=None)
        q.task_done()


b = threading.Thread(name='background', target=background)
f = threading.Thread(name='foreground', target=foreground)

b.start()
f.start()
