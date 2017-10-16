#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
  _\
  \
O O-O
 O O
  O

Raspberry Potter
Version 0.1.5

Use your own wand or your interactive Harry Potter wands to control the IoT.

Updated for OpenCV 3.2
If you have an older version of OpenCV installed, please uninstall fully (check your cv2 version in python) and then install OpenCV following the guide here (but using version 3.2):
https://imaginghub.com/projects/144-installing-opencv-3-on-raspberry-pi-3/documentation

Copyright (c) 2015-2017 Sean O'Brien.  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''
import io
import sys
sys.path.insert(1, '/usr/lib/python2.7/dist-packages/picamera')
import picamera
import numpy as np
import cv2
import threading
import math
import time
import pigpio

GPIOS = 32
MODES = ["INPUT", "OUTPUT", "ALT5", "ALT4", "ALT0", "ALT1", "ALT2", "ALT3"]

pi = pigpio.pi()

#pin for Powerswitch (Lumos,Nox)
switch_pin = 16
pi.set_mode(switch_pin,pigpio.OUTPUT)

#pin for Trinket (Colovario)
trinket_pin = 12
pi.set_mode(trinket_pin,pigpio.OUTPUT)

# Parameters for image processing
lk_params = dict( winSize  = (15,15),
                maxLevel = 2,
                criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
dilation_params = (5, 5)
movment_threshold = 80

Scan()

# Scan starts camera input and runs FindNewPoints
def Scan():
    cv2.namedWindow("Raspberry Potter")
    stream = io.BytesIO()
    cam = picamera.PiCamera()
    cam.resolution = (640, 480)
    cam.framerate = 24
    try:
        while True:
            FindNewPoints()
    except KeyboardInterrupt:
        End()
        exit

#FindWand is called to find all potential wands in a scene.  These are then tracked as points for movement.  The scene is reset every 3 seconds.
def FindNewPoints():
    global old_frame,old_gray,p0,mask,color,ig,img,frame
    try:
        try:
            old_frame = cam.capture(stream, format='jpeg')
        except:
            print("resetting points")
        data = np.fromstring(stream.getvalue(), dtype=np.uint8)
        old_frame = cv2.imdecode(data, 1)
        cv2.flip(old_frame,1,old_frame)
        old_gray = cv2.cvtColor(old_frame,cv2.COLOR_BGR2GRAY)
        #cv2.equalizeHist(old_gray,old_gray)
	    #old_gray = cv2.GaussianBlur(old_gray,(9,9),1.5)
        #dilate_kernel = np.ones(dilation_params, np.uint8)
        #old_gray = cv2.dilate(old_gray, dilate_kernel, iterations=1)

        #TODO: trained image recognition
        p0 = cv2.HoughCircles(old_gray,cv2.HOUGH_GRADIENT,3,100,param1=100,param2=30,minRadius=4,maxRadius=15)
        p0.shape = (p0.shape[1], 1, p0.shape[2])
        p0 = p0[:,:,0:2]
        mask = np.zeros_like(old_frame)
        ig = [[0] for x in range(20)]
        print("finding...")
        TrackWand()
	    #This resets the scene every three seconds
        threading.Timer(3, FindNewPoints).start()
    except:
        e = sys.exc_info()[1]
        print("FindWand Error: %s" % e )
        End()
        exit

def TrackWand():
    global old_frame,old_gray,p0,mask,color,ig,img,frame
    color = (0,0,255)
    try:
        old_frame = cam.capture(stream, format='jpeg')
    except:
        print("resetting points")
    data = np.fromstring(stream.getvalue(), dtype=np.uint8)
    old_frame = cv2.imdecode(data, 1)
    cv2.flip(old_frame,1,old_frame)
    old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
    #cv2.equalizeHist(old_gray,old_gray)
    #old_gray = cv2.GaussianBlur(old_gray,(9,9),1.5)
    #dilate_kernel = np.ones(dilation_params, np.uint8)
    #old_gray = cv2.dilate(old_gray, dilate_kernel, iterations=1)
    # Take first frame and find circles in it
    p0 = cv2.HoughCircles(old_gray,cv2.HOUGH_GRADIENT,3,100,param1=100,param2=30,minRadius=4,maxRadius=15)
    try:
        p0.shape = (p0.shape[1], 1, p0.shape[2])
        p0 = p0[:,:,0:2]
    except:
        print("No points found")
	# Create a mask image for drawing purposes
    mask = np.zeros_like(old_frame)

    while True:
        frame = cam.capture(stream, format='jpeg')
        data2 = np.fromstring(stream.getvalue(), dtype=np.uint8)
        frame = cv2.imdecode(data2, 1)
        cv2.flip(frame,1,frame)
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        #equalizeHist(frame_gray,frame_gray)
        #frame_gray = GaussianBlur(frame_gray,(9,9),1.5)
        #dilate_kernel = np.ones(dilation_params, np.uint8)
        #frame_gray = cv2.dilate(frame_gray, dilate_kernel, iterations=1)
        try:
            # calculate optical flow
            p1, st, err = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)
            # Select good points
            good_new = p1[st==1]
            good_old = p0[st==1]
            # draw the tracks
            for i,(new,old) in enumerate(zip(good_new,good_old)):
                a,b = new.ravel()
                c,d = old.ravel()
                # only try to detect gesture on highly-rated points (below 15)
                if (i<15):
                    IsGesture(a,b,c,d,i)
                    dist = math.hypot(a - c, b - d)
                    if (dist<movment_threshold):
                        cv2.line(mask, (a,b),(c,d),(0,255,0), 2)
                        cv2.circle(frame,(a,b),5,color,-1)
                        cv2.putText(frame, str(i), (a,b), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,255))
        except IndexError:
            print("Index error")
            End()
            break
        except:
            e = sys.exc_info()[0]
            print("TrackWand Error: %s" % e )
            End()
            break
        img = cv2.add(frame,mask)

        cv2.putText(img, "Press ESC to close.", (5, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255))
        cv2.imshow("Raspberry Potter", frame)

        # get next frame
        frame = cam.capture(stream, format='jpeg')
        data3 = np.fromstring(stream.getvalue(), dtype=np.uint8)
        frame = cv2.imdecode(data3, 1)

        # Now update the previous frame and previous points
        old_gray = frame_gray.copy()
        p0 = good_new.reshape(-1,1,2)

#Spell is called to translate a named spell into GPIO or other actions
def Spell(spell):
    #clear all checks
    ig = [[0] for x in range(15)]
    #Invoke IoT (or any other) actions here
    cv2.putText(mask, spell, (5, 25),cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,0,0))
    if (spell=="Colovaria"):
        print("GPIO trinket")
        pi.write(trinket_pin,0)
        time.sleep(1)
        pi.write(trinket_pin,1)
    elif (spell=="Lumos"):
        print("GPIO ON")
        pi.write(switch_pin,1)
    elif (spell=="Nox"):
        print("GPIO OFF")
        pi.write(switch_pin,0)
    print("CAST: %s" %spell)

#IsGesture is called to determine whether a gesture is found within tracked points
def IsGesture(a,b,c,d,i):
    print("point: %s" % i)
    #record basic movements - TODO: trained gestures
    if ((a<(c-5))&(abs(b-d)<1)):
        ig[i].append("left")
    elif ((c<(a-5))&(abs(b-d)<1)):
        ig[i].append("right")
    elif ((b<(d-5))&(abs(a-c)<5)):
        ig[i].append("up")
    elif ((d<(b-5))&(abs(a-c)<5)):
        ig[i].append("down")
    #check for gesture patterns in array
    astr = ''.join(map(str, ig[i]))
    if "rightup" in astr:
        Spell("Lumos")
    elif "rightdown" in astr:
        Spell("Nox")
    elif "leftdown" in astr:
        Spell("Colovaria")
    print(astr)

def End():
	cam.close()
	cv2.destroyAllWindows()
