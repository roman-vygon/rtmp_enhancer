import cv2
import threading, queue
import time
from twitchstream.outputvideo import TwitchBufferedOutputStream
from tensorflow import keras
import numpy as np
import os

output_dir = 'frames'
q = queue.Queue()

model = keras.models.load_model('models/generator.h5')
inputs = keras.Input((None, None, 3))
output = model(inputs)
model = keras.models.Model(inputs, output)

stream_addr = 'rtmp://192.168.1.6/live/test'
cap = cv2.VideoCapture(stream_addr)
print(cap.isOpened())

width = 640
height = 480
fps = 30.

last_frame = np.zeros((height, width, 3))


def twitch_stream():
    videostream = TwitchBufferedOutputStream(
        twitch_stream_key='live_151094258_mOH5qXYKHsj6PqrTazKFAiCboLUnKn',
        width=width,
        height=height,
        fps=fps,
        enable_audio=False,
        verbose=False)
    while True:
        if videostream.get_video_frame_buffer_state() < 30:
            videostream.send_video_frame(last_frame)


def background():
    while True:
        ret, frame = cap.read()
        if frame is not None:
            # cv2.imshow('frame', frame)
            q.put(frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()


def foreground():
    num = 0
    while True:
        frame = q.get()
        frame = frame / 255.0

        sr = model.predict(np.expand_dims(frame, axis=0))[0]

        sr = ((sr + 1) / 2.) * 255

        # Save the results:
        cv2.imwrite(os.path.join(output_dir, str(num) + '.png'), sr)
        num += 1
        q.task_done()


b = threading.Thread(name='background', target=background)
f = threading.Thread(name='foreground', target=foreground)

b.start()
f.start()
