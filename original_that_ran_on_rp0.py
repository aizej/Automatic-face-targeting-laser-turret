from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory
import time
import math
import cv2
import sys
import numpy as np
import os
print("importing model (1 min 30 sec)")
from deepface import DeepFace
from deepface.detectors import FaceDetector

print("turning off motion tracking (30sec)")
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


cuttoff_center_x = 0
cuttoff_center_y = 0
face_center_x =0
face_center_y =0
currently_used_frame_x = cam_width
currently_used_frame_y = cam_height


factory = PiGPIOFactory() #otevři cmd a dej sudo pigpiod
servo1_PIN = 12
servo2_PIN = 14
servo1 = Servo(servo1_PIN, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000, pin_factory = factory)
servo2 = Servo(servo2_PIN, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000, pin_factory = factory)





servo_arm_1_start_position_to_camera = [0,0,0]#x,y,z
servo_arm_1_start_angle_to_camera = [-3,-2] #x,z

horizontal_angle_of_camera = 62.2
vertical_angle_of_camera = 48.8
cam_fov_for_resolutions = {(1024,600):(1*horizontal_angle_of_camera,0.74683*vertical_angle_of_camera)}
obj=[]


def get_angle_position(pixels,distance=None): #negunguje?
    if distance == None:
        distance= 1
    #horizontal_angle = (90+horizontal_angle_of_camera)-horizontal_angle_of_camera*2*pixels[0]+servo_arm_1_start_angle_to_camera[1]
    #vertical_angle = (90+vertical_angle_of_camera)-vertical_angle_of_camera*2*pixels[1]-servo_arm_1_start_angle_to_camera[0]
    f_horizontal = horizontal_angle_of_camera - 2*horizontal_angle_of_camera*pixels[0] + 90+servo_arm_1_start_angle_to_camera[0]
    horizontal_x=servo_arm_1_start_position_to_camera[0]+math.cos(math.radians(f_horizontal))*distance
    horizontal_y=servo_arm_1_start_position_to_camera[1]+math.sin(math.radians(f_horizontal))*distance
    horizontal_angle=math.degrees(math.acos(horizontal_x/math.sqrt(horizontal_x**2+horizontal_y**2)))

    f_vertical = vertical_angle_of_camera - 2*vertical_angle_of_camera*pixels[1] + 90+servo_arm_1_start_angle_to_camera[1]
    vertical_x=servo_arm_1_start_position_to_camera[2]+math.cos(math.radians(f_vertical))*distance
    vertical_y=servo_arm_1_start_position_to_camera[0]+math.sin(math.radians(f_vertical))*distance
    vertical_angle=math.degrees(math.acos(vertical_x/math.sqrt(vertical_x**2+vertical_y**2)))
    return [horizontal_angle,vertical_angle]



def move_servo(servo, angle):
    servo.value = angle/90 - 1
    time.sleep(5)

def get_to_pos(x,y):
    #print(x,y)
    servo1.value = x/90 - 1
    servo2.value = y/90 - 1
    #time.sleep(2)


def limit_cuttoff_to_inframe(cam_height, cam_width, detector_feed_height, detector_feed_width, cuttoff_move_x, cuttoff_move_y):
    if cuttoff_move_y > (cam_height/2)-(detector_feed_height/2):
        cuttoff_move_y = (cam_height/2)-(detector_feed_height/2)
    if cuttoff_move_y < -((cam_height/2)-(detector_feed_height/2)):
        cuttoff_move_y = -((cam_height/2)-(detector_feed_height/2))
    
    if cuttoff_move_x > (cam_width/2)-(detector_feed_width/2):
        cuttoff_move_x = (cam_width/2)-(detector_feed_width/2)
    if cuttoff_move_x < -((cam_width/2)-(detector_feed_width/2)):
        cuttoff_move_x = -((cam_width/2)-(detector_feed_width/2))
    return cuttoff_move_x, cuttoff_move_y

def angle_test(x_value,y_value):
    cam_horizontal_angle,cam_vertical_angle = cam_fov_for_resolutions[(cam_width,cam_height)]
    angle_at_zero_x = 90 + cam_horizontal_angle/2 #plus protože servo se točí od prava do leva, pravo=0 stupnu
    angle_at_zero_y = 90 + cam_vertical_angle/2
    x_angle = angle_at_zero_x - x_value*cam_horizontal_angle
    y_angle = angle_at_zero_y - y_value*cam_vertical_angle
    x_angle += servo_arm_1_start_angle_to_camera[0]
    y_angle += servo_arm_1_start_angle_to_camera[1]
    return [x_angle,y_angle]
    
def test_servo():
    print("testing servo")
    horizontal_angle, vertical_angle = get_angle_position([0,0],200)
    get_to_pos(horizontal_angle, vertical_angle)
    time.sleep(2)
    horizontal_angle, vertical_angle = get_angle_position([1,0],200)
    get_to_pos(horizontal_angle, vertical_angle)
    time.sleep(2)
    horizontal_angle, vertical_angle = get_angle_position([1,1],200)
    get_to_pos(horizontal_angle, vertical_angle)
    time.sleep(2)
    horizontal_angle, vertical_angle = get_angle_position([0,1],200)
    get_to_pos(horizontal_angle, vertical_angle)
    time.sleep(2)
    get_to_pos(90,90)
    time.sleep(2)
    print("done testing servos \n")


#horizontal_angle, vertical_angle = get_angle_position([0.5,0.5],200)
#get_to_pos(horizontal_angle, vertical_angle)
test_servo()

for i in range(1000):
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
        detector_feed_frame = frame
    else:
        currently_used_frame_x = detector_feed_width
        currently_used_frame_y = detector_feed_height
        detector_feed_frame = frame[int((cam_height/2)-(detector_feed_height/2)+cuttoff_center_y):int((cam_height/2)+(detector_feed_height/2)+cuttoff_center_y), int((cam_width/2)-(detector_feed_width/2)+cuttoff_center_x):int((cam_width/2)+(detector_feed_width/2)+cuttoff_center_x)]
        # cropne frame 


    end_frame = time.time()
    start_detection_time = time.time()

    obj = FaceDetector.detect_faces(detector, detector_name, detector_feed_frame)

    end_detection = time.time()
    start_write_time = time.time()

    if obj != []:
        face_x_size_in_pixels = obj[0][1][2]
        face_y_size_in_pixels = obj[0][1][3]
        face_center_x += obj[0][1][0]+(face_x_size_in_pixels/2)-currently_used_frame_x/2
        face_center_y += obj[0][1][1]+(face_y_size_in_pixels/2)-currently_used_frame_y/2 #[sx,sy,ex,ey] střed = [sx+ex/2,-sy+ey/2]
        cuttoff_center_x, cuttoff_center_y = limit_cuttoff_to_inframe(cam_height=cam_height, cam_width=cam_width, detector_feed_height=detector_feed_height, detector_feed_width=detector_feed_width, cuttoff_move_x=face_center_x, cuttoff_move_y=face_center_y)
        face_position_x_to_frame = (face_center_x+cam_width/2)/cam_width
        face_position_y_to_frame = (face_center_y+cam_height/2)/cam_height
        face_test_angles = angle_test(face_position_x_to_frame,face_position_y_to_frame)
        #face_angles = get_angle_position(pixels=[face_position_x_to_frame,face_position_y_to_frame])
        get_to_pos(face_test_angles[0],face_test_angles[1])
        #print(face_position_x_to_frame,face_position_y_to_frame)
        #print(face_angles)
        #print(face_test_angles)
        
    """   
    if len(obj) == 1 or i == 0:
        cv2.imwrite(fr"/home/pi/Desktop/images/{i}_detector_frame.jpg", detector_feed_frame)
    else:
        cv2.imwrite(fr"/home/pi/Desktop/images/{i}_NO_detector_frame.jpg", detector_feed_frame)
    """ 
    end_write = time.time()
    print("\n",i)
    #print(currently_used_frame_x,currently_used_frame_y)
    #print("there are ",len(obj)," faces")
    #print("getting image: ",end_frame-start_frame_time)
    #print("face detection:",end_detection-start_detection_time)
    #print("zapis: ",end_write-start_write_time)
    print("čas_za_frame: ", end_write-start_frame_time)
    #print(time.time()-end_write)





video_capture.release()
cv2.destroyAllWindows()
