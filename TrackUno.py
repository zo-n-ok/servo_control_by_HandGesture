import time
import cv2
import mediapipe as mp
import numpy as np
import serial  # Import Serial library

# Initialize Serial Communication (Change 'COM3' to your Arduino port)
arduino = serial.Serial('COM3', 9600, timeout=1)
time.sleep(2)  # Wait for connection

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

last_change = time.time()

def send_command(direction):
    """Send command to Arduino to move servo motor"""
    global last_change
    if time.time() - last_change > 0.3:  # Cooldown to prevent rapid commands
        if direction == 'up':
            arduino.write(b'U')  # Send 'U' for up
            print("Servo Moving UP")
        elif direction == 'down':
            arduino.write(b'D')  # Send 'D' for down
            print("Servo Moving DOWN")
        last_change = time.time()

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

if not cap.isOpened():
    print("Error: Camera not accessible.")
    exit()

try:
    while True:
        success, img = cap.read()
        if not success:
            break

        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(imgRGB)

        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)
                
                lmList = []
                h, w, c = img.shape
                for id, lm in enumerate(handLms.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lmList.append([id, cx, cy])

                tipId, thumbTipId = 8, 4
                tipX, tipY = lmList[tipId][1], lmList[tipId][2]
                thumbTipX, thumbTipY = lmList[thumbTipId][1], lmList[thumbTipId][2]
                distance = ((tipX - thumbTipX)**2 + (tipY - thumbTipY)**2)**0.5

                cv2.line(img, (tipX, tipY), (thumbTipX, thumbTipY), (255, 0, 0), 3)
                midX, midY = (tipX + thumbTipX) // 2, (tipY + thumbTipY) // 2
                cv2.circle(img, (midX, midY), 5, (255, 0, 0), -1)

                if distance < 40:
                    send_command('down')  # Move servo down
                elif distance > 80:
                    send_command('up')  # Move servo up

        cv2.imshow("Hand Tracker", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    arduino.close()
    cap.release()
    cv2.destroyAllWindows()
