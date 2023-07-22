from gpiozero import Servo,TonalBuzzer,DigitalOutputDevice
from gpiozero.pins.pigpio import PiGPIOFactory
from buzzer import play_tone_nice, play_tone_fail
import time
import math
import cv2
import sys
import numpy as np
import os
import threading

start_import = time.time()
print("importing model:")
from deepface import DeepFace
from deepface.detectors import FaceDetector
print("model imported")



print("turning off motion tracking")
os.system("sudo service motion stop")#sudo service motion stop
os.system("sudo killall pigpiod")
os.system("sudo pigpiod")
time.sleep(5)
print("got factory")

detector_name = "opencv" #otestovat jeste dlib, opencv,retinaface
detector = FaceDetector.build_model(detector_name)
print("got detector")

cam_width = 1024  #1024
cam_height = 600  #600
detector_feed_height = 150 #214
detector_feed_width = 150 #300
video_capture = cv2.VideoCapture(0)
video_capture.set(3,cam_width) #width=224 0.3sec
video_capture.set(4,cam_height) #height=224
print(f"got camera: {cam_width}:{cam_height}")

factory = PiGPIOFactory() #otevři cmd a dej sudo pigpiod
SERVO1_PIN = 12
SERVO2_PIN = 13
BZUCAK_PIN = 14
LASER_PIN = 17
laser = DigitalOutputDevice(LASER_PIN)
buzzer = TonalBuzzer(BZUCAK_PIN)
servo1 = Servo(SERVO1_PIN, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000, pin_factory = factory)
servo2 = Servo(SERVO2_PIN, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000, pin_factory = factory)
buzzer_nice = threading.Thread(target=play_tone_nice,args=(buzzer,),daemon=True)

print(f"Done: got all in: {round(time.time()-start_import,1)}s")
play_tone_nice(buzzer)





cuttoff_center_x = 0
cuttoff_center_y = 0
face_center_x = 0
face_center_y = 0
currently_used_frame_x = cam_width
currently_used_frame_y = cam_height

servo_arm_1_start_position_to_camera = [0,0,9]#x,y,z
servo_arm_1_start_angle_to_camera = [3.5,-48] #x,z

horizontal_angle_of_camera = 62.2
vertical_angle_of_camera = 48.8
cam_fov_for_resolutions = {(1024,600):(1*horizontal_angle_of_camera,0.74683*vertical_angle_of_camera)}
obj=[]








def move_servo(servo, angle):
    servo.value = angle/90 - 1
    return angle

def get_to_pos(x,y):
    servo1.value = x/90 - 1
    servo2.value = y/90 - 1
    return x, y

def get_to_pos_slow(servo1, servo2, position1, position2, angle1, angle2, speed=5):
    to_move1 = angle1 - position1
    to_move2 = angle2 - position2
    

    while position1 != angle1 or position2 != angle2:
        if position1 != angle1:
            if abs(position1-angle1)>=1:
                position1 += to_move1/abs(to_move1)
                move_servo(servo1,position1)
            else:
                move_servo(servo1,angle1)
                position1 = angle1
            
        if position2 != angle2:
            if abs(position2-angle2)>=1:
                position2 += to_move2/abs(to_move2)
                move_servo(servo2,position2)
            else:
                move_servo(servo2,angle2)
                position2 = angle2
        
        time.sleep(speed/180)

    return angle1, angle2

def calculate_angle_2D(x_value,y_value):
    cam_horizontal_angle,cam_vertical_angle = cam_fov_for_resolutions[(cam_width,cam_height)]
    angle_at_zero_x = 90 + cam_horizontal_angle/2 #plus protože servo se točí od prava do leva, pravo=0 stupnu
    angle_at_zero_y = 90 + cam_vertical_angle/2
    x_angle = angle_at_zero_x - x_value*cam_horizontal_angle
    y_angle = angle_at_zero_y + y_value*cam_vertical_angle
    x_angle += servo_arm_1_start_angle_to_camera[0]
    y_angle += servo_arm_1_start_angle_to_camera[1]
    return [x_angle,y_angle]

def test_servo():
    print("\ntesting servo")
    position1,position2 = get_to_pos(90,90)
    position1,position2 = get_to_pos_slow(servo1,servo2,position1,position2,110,110)
    position1,position2 = get_to_pos_slow(servo1,servo2,position1,position2,90+horizontal_angle_of_camera/2,90+vertical_angle_of_camera/2)
    position1,position2 = get_to_pos_slow(servo1,servo2,position1,position2,90+horizontal_angle_of_camera/2,90-vertical_angle_of_camera/2)
    position1,position2 = get_to_pos_slow(servo1,servo2,position1,position2,90-horizontal_angle_of_camera/2,90-vertical_angle_of_camera/2)
    position1,position2 = get_to_pos_slow(servo1,servo2,position1,position2,90-horizontal_angle_of_camera/2,90+vertical_angle_of_camera/2)
    position1,position2 = get_to_pos_slow(servo1,servo2,position1,position2,90+horizontal_angle_of_camera/2,90+vertical_angle_of_camera/2)
    position1,position2 = get_to_pos_slow(servo1,servo2,position1,position2,90,90)
    print("everithing ready!")









laser.on()
test_servo()
play_tone_nice(buzzer)


for i in range(100):
    # Capture frame-by-frame
    start_frame_time = time.time()


    ret, frame = video_capture.read()
    
    if obj == []:
        face_center_x =0            #all reset
        face_center_y =0            
        cuttoff_center_x = 0
        cuttoff_center_y = 0

        currently_used_frame_x = cam_width
        currently_used_frame_y = cam_height

    end_frame = time.time()
    start_detection_time = time.time()


    obj = FaceDetector.detect_faces(detector, detector_name, frame)


    end_detection = time.time()
    start_servo_time = time.time()


    if obj != []:
        face_x_size_in_pixels = obj[0][1][2]
        face_y_size_in_pixels = obj[0][1][3]
        face_center_x_to_frame = (obj[0][1][0]+(face_x_size_in_pixels/2))/currently_used_frame_x
        face_center_y_to_frame = (obj[0][1][1]+(face_y_size_in_pixels/2))/currently_used_frame_y #[sx,sy,ex,ey] střed = [sx+ex/2,-sy+ey/2]
        face_angles = calculate_angle_2D(face_center_x_to_frame,face_center_y_to_frame)
        get_to_pos(face_angles[0],face_angles[1])
        #buzzer_nice = threading.Thread(target=play_tone_nice,args=(buzzer,),daemon=True)
        #-buzzer_nice.start()
        #print(face_center_x,face_center_y)
    

    end_write = time.time()
    print("\n",i)
    #print(currently_used_frame_x,currently_used_frame_y)
    #print("there are ",len(obj)," faces")
    #print("getting image: ",end_frame-start_frame_time)
    #print("face detection:",end_detection-start_detection_time)
    #print("zapis: ",end_write-start_servo_time)
    print("čas_za_frame: ", end_write-start_frame_time)
    #print(time.time()-end_write)





laser.off()
video_capture.release()
cv2.destroyAllWindows()
