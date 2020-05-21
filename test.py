import cv2
import threading
import time

frames = []
stream_addr = 'rtmp://192.168.1.6/live/test'
cap = cv2.VideoCapture(stream_addr)
print(cap.isOpened())

def background():
    while True:
        ret, frame = cap.read()
        if frame is not None:
            cv2.imshow('frame', frame)
            frames.append(frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

def foreground():
    while True:
        time.sleep(1)
        print(len(frames))


b = threading.Thread(name='background', target=background)
f = threading.Thread(name='foreground', target=foreground)


b.start()
f.start()

