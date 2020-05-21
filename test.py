import cv2

stream_addr = 'rtmp://192.168.1.6/live/test'
cap = cv2.VideoCapture(stream_addr)

while (True):
    ret, frame = cap.read()
    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()