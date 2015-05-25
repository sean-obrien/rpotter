#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Raspberry
    _ __
   | '  \
   | .-. \        /|
   | | | |      ,' |_   /|
   | |_| |   _ '-. .-',' |_   _
   |     | ,'_`. | | '-. .-',' `. ,'\_
  .| |\_/ | / \ || |   | | / |\  \|   \
  |  |    | | | || |   | | | |_\ || |\_|
  | |`    | | | || |   | | | .---'| |
  | |     | \_/ || |   | | | |  /\| |
 .||`      `._,' | |   | | \ `-' /| |
 \ |              `.\  | |  `._,' /_\
  \|                   `.\

Version 0.1

Use your interactive Harry Potter wands to control the IoT.  


Copyright (c) 2015 Sean O'Brien

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''
import cv2
import numpy as np
import threading
import sys
import math

print "Initializing point tracking"

# Parameters
lk_params = dict( winSize  = (15,15),
                  maxLevel = 2,
                  criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
blur_params = (9,9)
dilation_params = (5, 5)
movment_threshold = 80

# start capturing
cam = cv2.VideoCapture(0)
cv2.namedWindow("Raspberry Potter")

def Spell(spell):    
    #clear all checks
    ig = [[0] for x in range(15)] 
    #Invoke IoT (or any other) actions here
    cv2.putText(mask, spell, (5, 25),cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,0,0))
    print "CAST: %s" %spell

def IsGesture(a,b,c,d,i):
    print "point: %s" % i
    #record basic movements - TODO: trained gestures
    #for z in ig[i]:
    #    print z
    if ((a<(c-5))&(abs(b-d)<1)):
        ig[i].append("right")
    #    print "right"
    elif ((c<(a-5))&(abs(b-d)<1)):
        ig[i].append("left")
    #    print "left"  
    elif ((b<(d-5))&(abs(a-c)<5)):
        ig[i].append("up")
    #    print "up" 
    elif ((d<(b-5))&(abs(a-c)<5)):
        ig[i].append("down")
    #    print "down"       
    #check for gesture patterns in array
    astr = ''.join(map(str, ig[i]))
    if "rightup" in astr:
        Spell("Lumos")
    elif "rightdown" in astr:
        Spell("Nox")
    elif "leftdown" in astr:
        Spell("Colovaria")
    print astr
    
def FindWand():
    global rval,old_frame,old_gray,p0,mask,color,ig,img,frame
    try:  
        rval, old_frame = cam.read()
        old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
        
        # adaptive histogram equalization
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(3,3))
        old_gray = clahe.apply(old_gray)
        old_gray = cv2.GaussianBlur(old_gray,blur_params,2,2);

        # dilate
        dilate_kernel = np.ones(dilation_params, np.uint8)
        dilate_kernel = np.ones(dilation_params, np.uint8)
        old_gray = cv2.dilate(old_gray, dilate_kernel, iterations=1)

        #TODO: trained image recognition
        p0 = cv2.HoughCircles(old_gray,cv2.cv.CV_HOUGH_GRADIENT,3,100,param1=100,param2=30,minRadius=5,maxRadius=15)
        p0.shape = (p0.shape[1], 1, p0.shape[2])
        p0 = p0[:,:,0:2]  
        mask = np.zeros_like(old_frame)
        ig = [[0] for x in range(15)] 
        print "finding..."
        threading.Timer(3, FindWand).start()
    except:
        cv2.destroyAllWindows()
        cam.release()  
        exit
        
def TrackWand():
    if cam.isOpened(): # try to get the first frame
        # Take first frame and find circles in it
        global rval,old_frame,old_gray,p0,mask,color,ig,img,frame
        color = (0,0,255)
        rval, old_frame = cam.read()
        old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
        # adaptive histogram equalization
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(3,3))
        old_gray = clahe.apply(old_gray)
        old_gray = cv2.GaussianBlur(old_gray,blur_params,2,2);

        # dilate
        dilate_kernel = np.ones(dilation_params, np.uint8)
        old_gray = cv2.dilate(old_gray, dilate_kernel, iterations=1)
        p0 = cv2.HoughCircles(old_gray,cv2.cv.CV_HOUGH_GRADIENT,3,100,param1=100,param2=30,minRadius=5,maxRadius=15)
        p0.shape = (p0.shape[1], 1, p0.shape[2])
        p0 = p0[:,:,0:2]    
        # Create a mask image for drawing purposes
        mask = np.zeros_like(old_frame)
    else:
        rval = False

    while rval:
        rval,frame = cam.read()
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # adaptive histogram equalization
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(3,3))
        frame_gray = clahe.apply(frame_gray)
        frame_gray = cv2.GaussianBlur(frame_gray,blur_params,2,2);

        # dilate
        dilate_kernel = np.ones(dilation_params, np.uint8)
        frame_gray = cv2.dilate(frame_gray, dilate_kernel, iterations=1)
        
        # calculate optical flow
        p1, st, err = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)

        # Select good points
        try:
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
            print "Index error"           
        except:
            e = sys.exc_info()[0]
            print "Error: %s" % e 
        img = cv2.add(frame,mask)

        cv2.putText(img, "Press ESC to close.", (5, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255))
        cv2.imshow("Raspberry Potter", img)

        # get next frame
        rval, frame = cam.read()

        # Now update the previous frame and previous points
        old_gray = frame_gray.copy()
        p0 = good_new.reshape(-1,1,2)
        key = cv2.waitKey(20)
        if key in [27, ord('Q'), ord('q')]: # exit on ESC
            break
            
FindWand()
TrackWand()            
cv2.destroyAllWindows()
cam.release()  

