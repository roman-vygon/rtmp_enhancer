# This script copies the video frame by frame
import cv2
import subprocess as sp
import time
import numpy as np
import queue
import threading
twitch_stream_key = 'live_151094258_mOH5qXYKHsj6PqrTazKFAiCboLUnKn'

command = []
command.extend([
    'FFMPEG',
    '-loglevel', 'verbose',
    '-y',  # overwrite previous file/stream
    '-analyzeduration', '1',
    '-f', 'rawvideo',
    '-r', '%d' % 30.,  # set a fixed frame rate
    '-vcodec', 'rawvideo',
    # size of one frame
    '-s', '%dx%d' % (640, 480),
    '-pix_fmt', 'rgb24',  # The input are raw bytes
    '-thread_queue_size', '1024',
    '-i', '-',  # The input comes from a pipe

])
command.extend([
    '-ar', '8000',
    '-ac', '1',
    '-f', 's16le',
    '-i', 'http://www.hochmuth.com/mp3/Tchaikovsky_Nocturne__orch.mp3',
])
command.extend([
    # VIDEO CODEC PARAMETERS
    '-vcodec', 'libx264',
    '-r', '%d' % 30.,
    '-b:v', '3000k',
    '-s', '%dx%d' % (640, 480),
    '-preset', 'faster', '-tune', 'zerolatency',
    '-crf', '23',
    '-pix_fmt', 'yuv420p',

    '-minrate', '3000k', '-maxrate', '3000k',
    '-bufsize', '12000k',
    '-g', '60',  # key frame distance
    '-keyint_min', '1',

    # AUDIO CODEC PARAMETERS
    '-acodec', 'libmp3lame', '-ar', '44100', '-b:a', '160k',
    # '-bufsize', '8192k',
    '-ac', '1',
    '-map', '0:v', '-map', '1:a',

    '-threads', '2',
    # STREAM TO TWITCH
    '-f', 'flv', 'rtmp://live-hel.twitch.tv/app/%s' %
          twitch_stream_key
])


class Streamer:
    def __init__(self, height, width, fps):
        self.ffmpeg = 'FFMPEG'
        self.dimension = '{}x{}'.format(width, height)
        self.f_format = 'bgr24'
        self.fps = fps

        self.height = height
        self.width = width

        self.last_frame = np.ones((self.height, self.width, 3))

        self.last_frame_time = None
        self.next_video_send_time = None
        self.frame_counter = 0
        self.q_video = queue.PriorityQueue()

        self.proc = sp.Popen(command, stdin=sp.PIPE)

        self.t = threading.Timer(0.0, self._send_video_frame)
        self.t.daemon = True
        self.t.start()

    def get_video_frame_buffer_state(self):
        """Find out how many video frames are left in the buffer.
        The buffer should never run dry, or audio and video will go out
        of sync. Likewise, the more filled the buffer, the higher the
        memory use and the delay between you putting your frame in the
        stream and the frame showing up on Twitch.
        :return integer estimate of the number of video frames left.
        """
        return self.q_video.qsize()

    def send_video_frame(self, frame):
        """Send frame of shape (height, width, 3)
        with values between 0 and 1.
        Raises an OSError when the stream is closed.
        :param frame: array containing the frame.
        :type frame: numpy array with shape (height, width, 3)
            containing values between 0.0 and 1.0
        """
        assert frame.shape == (self.height, self.width, 3)

        frame = np.clip(255 * frame, 0, 255).astype('uint8')
        try:
            self.proc.stdin.write(frame.tostring())
        except OSError:
            # The pipe has been closed. Reraise and handle it further
            # downstream
            raise

    def _send_video_frame(self):
        start_time = time.time()
        try:
            frame = self.q_video.get_nowait()
            # frame[0] is frame count of the frame
            # frame[1] is the frame
            frame = frame[1]
        except IndexError:
            frame = self.last_frame
        except queue.Empty:
            frame = self.last_frame
        else:
            self.last_frame = frame

        try:
            send_video_frame(frame)
        except OSError:
            # stream has been closed.
            # This function is still called once when that happens.
            # Don't call this function again and everything should be
            # cleaned up just fine.
            return

        # send the next frame at the appropriate time
        if self.next_video_send_time is None:
            self.t = threading.Timer(1. / self.fps, self._send_video_frame)
            self.next_video_send_time = start_time + 1. / self.fps
        else:
            self.next_video_send_time += 1. / self.fps
            next_event_time = self.next_video_send_time - start_time
            if next_event_time > 0:
                self.t = threading.Timer(next_event_time,
                                         self._send_video_frame)
            else:
                self.t = threading.Thread(
                    target=self._send_video_frame)

        self.t.daemon = True
        self.t.start()

    def __exit__(self):
        self.proc.stdin.close()
        self.proc.stderr.close()
        self.proc.wait()


stream = Streamer(480, 640, 30)

while True:
    if stream.get_video_frame_buffer_state() < 30:
        frame = np.random.rand(480, 640, 3)
        stream.send_video_frame(frame)
