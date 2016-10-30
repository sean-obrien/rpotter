#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
  _\
  \
O O-O
 O O
  O
  
Raspberry Potter
Ollivander - Version 0.2 

Use your own wand or your interactive Harry Potter wands to control the IoT.  


Copyright (c) 2016 Sean O'Brien.  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''
import io
import numpy as np
import argparse
import cv2
from cv2 import *
import picamera
import threading
import sys
import math
import time
import pigpio
import warnings

warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)

GPIOS=32
MODES=["INPUT", "OUTPUT", "ALT5", "ALT4", "ALT0", "ALT1", "ALT2", "ALT3"]

pi = pigpio.pi()

#NOTE pins use BCM numbering in code.  I reference BOARD numbers in my articles - sorry for the confusion!

#pin for Powerswitch (Lumos,Nox)
switch_pin = 23
pi.set_mode(switch_pin,pigpio.OUTPUT)

#pin for Particle (Nox)
nox_pin = 24
pi.set_mode(nox_pin,pigpio.OUTPUT)

#pin for Particle (Incendio)
incendio_pin = 22
pi.set_mode(incendio_pin,pigpio.OUTPUT)

#pin for Trinket (Colovario)
trinket_pin = 12
pi.set_mode(trinket_pin,pigpio.OUTPUT)

print "Initializing point tracking"

# Parameters
lk_params = dict( winSize  = (15,15),
                  maxLevel = 2,
                  criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
blur_params = (4,4)
dilation_params = (5, 5)
movment_threshold = 80

print "START switch_pin ON for pre-video test"
pi.write(nox_pin,0)
pi.write(incendio_pin,0)
pi.write(switch_pin,1)

# start capturing
cv2.namedWindow("Raspberry Potter")
cam = cv2.VideoCapture(-1)
cam.set(3, 640)
cam.set(4, 480)


def Spell(spell):    
    #clear all checks
    ig = [[0] for x in range(15)] 
    #Invoke IoT (or any other) actions here
    cv2.putText(mask, spell, (5, 25),cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,0,0))
    if (spell=="Colovaria"):
	print "trinket_pin trigger"
	pi.write(trinket_pin,0)
	time.sleep(1)
	pi.write(trinket_pin,1)
    elif (spell=="Incendio"):
	print "switch_pin OFF"
	pi.write(switch_pin,0)
	print "nox_pin OFF"
	pi.write(nox_pin,0)
	print "incendio_pin ON"
	pi.write(incendio_pin,1)
    elif (spell=="Lumos"):
	print "switch_pin ON"
	pi.write(switch_pin,1)
	print "nox_pin OFF"
	pi.write(nox_pin,0)
	print "incendio_pin OFF"
	pi.write(incendio_pin,0)	
    elif (spell=="Nox"):
	print "switch_pin OFF"
	pi.write(switch_pin,0)
	print "nox_pin ON"
	pi.write(nox_pin,1)
	print "incendio_pin OFF"
	pi.write(incendio_pin,0)	
    print "CAST: %s" %spell
    

def IsGesture(a,b,c,d,i):
    print "point: %s" % i
    #look for basic movements - TODO: trained gestures
    if ((a<(c-5))&(abs(b-d)<2)):
        ig[i].append("left")
    elif ((c<(a-5))&(abs(b-d)<2)):
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
    elif "leftup" in astr:
        Spell("Incendio")    
    print astr
    
def FindWand():
    global rval,old_frame,old_gray,p0,mask,color,ig,img,frame
    try:
        rval, old_frame = cam.read()
	cv2.flip(old_frame,1,old_frame)
        old_gray = cv2.cvtColor(old_frame,cv2.COLOR_BGR2GRAY)
        equalizeHist(old_gray)
	old_gray = GaussianBlur(old_gray,(9,9),1.5)
        dilate_kernel = np.ones(dilation_params, np.uint8)
        old_gray = cv2.dilate(old_gray, dilate_kernel, iterations=1)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        old_gray = clahe.apply(old_gray)
        #TODO: trained image recognition
        p0 = cv2.HoughCircles(old_gray,cv2.HOUGH_GRADIENT,3,50,param1=240,param2=8,minRadius=4,maxRadius=15)
	if p0 is not None:
            p0.shape = (p0.shape[1], 1, p0.shape[2])
            p0 = p0[:,:,0:2] 
            mask = np.zeros_like(old_frame)
            ig = [[0] for x in range(20)]
        print "finding..."
        threading.Timer(3, FindWand).start()
    except:
        e = sys.exc_info()[1]
        print "Error: %s" % e 
        exit
        
def TrackWand():
        global rval,old_frame,old_gray,p0,mask,color,ig,img,frame
        try:
                color = (0,0,255)
                rval, old_frame = cam.read()
                cv2.flip(old_frame,1,old_frame)
                old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
                equalizeHist(old_gray)
                old_gray = GaussianBlur(old_gray,(9,9),1.5)
                dilate_kernel = np.ones(dilation_params, np.uint8)
                old_gray = cv2.dilate(old_gray, dilate_kernel, iterations=1)
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                old_gray = clahe.apply(old_gray)

                # Take first frame and find circles in it
                p0 = cv2.HoughCircles(old_gray,cv2.HOUGH_GRADIENT,3,50,param1=240,param2=8,minRadius=4,maxRadius=15)
                if p0 is not None:
                    p0.shape = (p0.shape[1], 1, p0.shape[2])
                    p0 = p0[:,:,0:2]
                    mask = np.zeros_like(old_frame)
        except:
            	print "No points found"         
	# Create a mask image for drawing purposes
        
	while True:
                try: 
                        rval, frame = cam.read()
                        cv2.flip(frame,1,frame)
			if p0 is not None:
                            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                            equalizeHist(frame_gray)
                            frame_gray = GaussianBlur(frame_gray,(9,9),1.5)
                            dilate_kernel = np.ones(dilation_params, np.uint8)
                            frame_gray = cv2.dilate(frame_gray, dilate_kernel, iterations=1)    
                            frame_clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                            frame_gray = frame_clahe.apply(frame_gray)

                        # calculate optical flow
                            p1, st, err = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)

                        # Select good points
                            good_new = p1[st==1]
                            good_old = p0[st==1]

                            # draw the tracks
                            for i,(new,old) in enumerate(zip(good_new,good_old)):
                                    a,b = new.ravel()
                                    c,d = old.ravel()
                                    # only try to detect gesture on highly-rated points (below 10)
                                    if (i<15):
                                            IsGesture(a,b,c,d,i)
                                    dist = math.hypot(a - c, b - d)
                                    if (dist<movment_threshold):
                                            cv2.line(mask, (a,b),(c,d),(0,255,0), 2)
                                    cv2.circle(frame,(a,b),5,color,-1)
                                    cv2.putText(frame, str(i), (a,b), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,255)) 
                            img = cv2.add(frame,mask)

                            cv2.putText(img, "Press ESC to close.", (5, 25),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255))
                        cv2.imshow("Raspberry Potter", frame)

                        # get next frame
                        rval, frame = cam.read()

                        # Now update the previous frame and previous points
                        old_gray = frame_gray.copy()
                        p0 = good_new.reshape(-1,1,2)
                except IndexError:
            		print "Index error - Tracking"  
        	except:
            		e = sys.exc_info()[0]
            		print "Tracking Error: %s" % e 
        	key = cv2.waitKey(20)
        	if key in [27, ord('Q'), ord('q')]: # exit on ESC
                        cv2.destroyAllWindows()
                        cam.release()  
            		break           

try:
    FindWand()
    print "START incendio_pin ON and set switch off if video is running"
    pi.write(incendio_pin,1)
    pi.write(switch_pin,0)      
    TrackWand()  
finally:   
    cv2.destroyAllWindows()
    cam.release()  
