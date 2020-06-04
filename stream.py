# This script copies the video frame by frame
import cv2
import subprocess as sp
twitch_stream_key = 'live_151094258_mOH5qXYKHsj6PqrTazKFAiCboLUnKn'
input_file = 'video.mkv'

cap = cv2.VideoCapture(input_file)
ret, frame = cap.read()
height, width, ch = frame.shape

ffmpeg = 'FFMPEG'
dimension = '{}x{}'.format(width, height)
f_format = 'bgr24' # remember OpenCV uses bgr format
fps = cap.get(cv2.CAP_PROP_FPS)
command = []
command.extend([
            'FFMPEG',
            '-loglevel', 'verbose',
            '-y',  # overwrite previous file/stream            
            '-analyzeduration', '1',
            '-f', 'rawvideo',
            '-r', '%d' % fps,  # set a fixed frame rate
            '-vcodec', 'rawvideo',
            # size of one frame
            '-s', '%dx%d' % (width, height),
            '-pix_fmt', 'rgb24',  # The input are raw bytes
            '-thread_queue_size', '4096',
            '-i', '-',  # The input comes from a pipe
            
        ])       
command.extend([
    '-ar', '8000',
    '-ac', '1',
    '-f', 's16le',                
    '-i', 'work.mp3',                
])
command.extend([
    # VIDEO CODEC PARAMETERS
    '-vcodec', 'libx264',
    '-r', '%d' % fps,
    '-b:v', '3000k',
    '-s', '%dx%d' % (width, height),
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
proc = sp.Popen(command, stdin=sp.PIPE)

while True:
    ret, frame = cap.read()
    if not ret:        
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    else:
        proc.stdin.write(frame.tostring())
    
    #text_file = open("sample.txt", "a")
    #for line in proc.stdout:        
    #    n = text_file.write(line)
    #text_file.close()

cap.release()
proc.stdin.close()
proc.stderr.close()
proc.wait()