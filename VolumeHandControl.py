import cv2
import time
import numpy as np
import math
import mediapipe as mp
# Pycaw
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


# Get the speakers
#######################
device = AudioUtilities.GetSpeakers()
interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
volRange = volume.GetVolumeRange()
#######################


# Make the window
#######################
scale = 1
wCam, hCam = 1280 * scale, 720 * scale
#######################


# Get the camera
#######################
camera = cv2.VideoCapture(0)
camera.set(3, wCam)
camera.set(4, hCam)
pTime = 0
#######################


# Hand Class
#######################
class handDetector():
    def __init__(self, mode = False, maxHands = 2, detectionCon = 0.5, trackCon = 0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(self.mode, self.maxHands, self.detectionCon, self.detectionCon)
        self.mpDraw = mp.solutions.drawing_utils
        self.tipIds = [4, 8, 12, 16, 20]

    def findHands(self, img, draw = True):

        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
                

        return img
    
    def findPosition(self, img, handNo = 0, draw = False):
        self.lmList = []

        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]

            for id, lm in enumerate(myHand.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x*w), int(lm.y*h)
                self.lmList.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 15, (225,0,225), cv2.FILLED)


        return self.lmList
                
    def fingersUp(self):
        fingers = []
        #Thumb
        if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)
        #4 Fingers
        for id in range(1, 5):
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        return fingers
#######################


# Get the hand
#######################
detector = handDetector(detectionCon = 0.8)
#######################

# The values for sound
#######################
values = [-50,-45.62559509,-42.23281097,-39.46084976,-37.11726761,-35.08721542,-33.29661942,-31.69490242,
        -30.24598885,-28.92324829,-27.70645523,-26.5798893,-25.53108788,-24.55000496,-23.62842369,-22.75953674,
        -21.93764496,-21.15792084,-20.41625023,-19.70909309,-19.03337479,-18.38642311,-17.7658844,-17.16968918,
        -16.59599876,-16.04317474,-15.50975323,-14.99441719,-14.49598217,-14.01337337,-13.54561615,-13.09182644,
        -12.65119171,-12.22297001,-11.80648327,-11.40110493,-11.0062561,-10.62140656,-10.24606037,-9.879759789,
        -9.52207756,-9.172620773,-8.831016541,-8.496921539,-8.17001152,-7.8499856,-7.536557674,-7.2294631,
        -6.928450108,-6.633281708,-6.343736649,-6.059604168,-5.780685902,-5.506793022,-5.237746716,-4.973381519,
        -4.713535786,-4.458057404,-4.206802368,-3.959632635,-3.716416597,-3.477032423,-3.241359711,-3.009285212,
        -2.780700922,-2.55550313,-2.333591938,-2.114875078,-1.899260759,-1.686662078,-1.476996064,-1.270182729,
        -1.066144347,-0.864809752,-0.666107118,-0.469968468,-0.276328534,-0.085124426,0.104416773,0.2958664,
        0.489757001,0.686152756,0.885119379,1.086724877,1.291040421,1.498140931,1.708100915,1.921001673,
        2.136926889,2.355963469,2.578202724,2.803740978,3.032674551,3.265109062,3.501152992,3.740920544,
        3.984530687,4.2321105,4.483787537,4.739702702, 5]
#######################

# Sets the sound
#######################
def setSoundLevel(value):
    value = int(5*(value//5))
    try:
        if round(volume.GetMasterVolumeLevel(),2) != round(values[value],2):
            print(f"Volume set to: {value}%")
            volume.SetMasterVolumeLevelScalar(value/100, None)
    except:
        pass
#######################


# Draws the line between the index finger and thumb, 
# makes a cricle in the middle 
# and finds the distances between the the nodes at the base of the fingers
# This will give us a proportion in case the hand moves closer to the camera or otherwise
#######################
def drawLine(img, lmList):

    #tip thumb, index
    x1, y1, x2, y2 = lmList[4][1], lmList[4][2], lmList[8][1], lmList[8][2]
    distance = math.hypot(x2 - x1, y2 - y1)

    #base thumb, index
    x3, y3, x4, y4 = lmList[2][1], lmList[2][2], lmList[5][1], lmList[5][2] 
    distanceStart = math.hypot(x4 - x3, y4 - y3)

    distance = int(distance / distanceStart * 100 * scale) 

    centerx, centery = (x1 + x2) // 2 , (y1 + y2) // 2

    distance = int(distance)

    # Draw the points & the line
    cv2.circle(img, (x1, y1), int(15 * scale), (255,0,255), cv2.FILLED)
    cv2.circle(img, (x2, y2), int(15 * scale), (255,0,255), cv2.FILLED)
    cv2.circle(img, (centerx, centery), int(10 * scale), (255,0,255), cv2.FILLED)
    cv2.line(img, (x1, y1), (x2, y2), (255,0,255), 3)

    # Draw the rectangle showing the level
    vol = np.interp(distance, [int(60 * scale), int(190 * scale)], [int(400 * scale), int(150 * scale)])
    cv2.rectangle(img, (int(50 * scale), int(150 * scale)), (int(85 * scale), int(400 * scale)), (0, 255, 0), 3)
    cv2.rectangle(img, (int(50 * scale), int(vol)), (int(85 * scale), int(400 * scale)), (0, 255, 0), cv2.FILLED)

    return img, distance, centerx, centery
#######################

if __name__ == "__main__":
    while True:
        success, img = camera.read()
        
        img = detector.findHands(img)
        lmList = detector.findPosition(img)

        if len(lmList):
            img, distance, centerx, centery = drawLine(img, lmList)

            volValue = np.interp(distance, [int(60 * scale), int(190 * scale)], [0, 100])
            volValue = volValue//5*5
            cv2.putText(img, f'{int(volValue)}%', (int(40 * scale), int(500 * scale)), cv2.FONT_HERSHEY_PLAIN, 3, (0,255,0), 3)
            
            fingers = detector.fingersUp()
            if fingers[4] == 0 and sum(fingers) > 2:
                cv2.circle(img, (centerx, centery), int(10 * scale), (0,255,0), cv2.FILLED)
                setSoundLevel(volValue)
            elif sum(fingers) == 0:
                setSoundLevel(20)
        else:
            setSoundLevel(20)

        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime

        cv2.putText(img, f'FPS: {int(fps)}', (int(40 * scale), int(70 * scale)), cv2.FONT_HERSHEY_PLAIN, 3, (225,0,0), 3)

        cv2.imshow("Hand Volume", img)
        cv2.waitKey(2)