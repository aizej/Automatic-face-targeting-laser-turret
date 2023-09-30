# Automatic-face-targeting-laser-turret
 This is a recreation of my old project that used raspberry pi 0 to detect faces through a small camera and directed servos to aim a laser at that face.
 This recreation is now made with raspberry pi 4 


This is the hardware setup:
2 servos (Waveshare MG996R servo)
camera (Raspberry Pi Camera V2)
laser module (KY-008)
buzzer (FC-07)
![20230720_230509](https://github.com/aizej/Face-targeting-laser-turret/assets/61479273/fb9b24dd-068c-4ebf-9de9-db6f57d319f7)

And here is what it can do with the simple 2D_no_optimatization software:
https://github.com/aizej/Face-targeting-laser-turret/assets/61479273/417483f3-e175-42ac-8c8f-4eb6831cfa0c

Now for the code:

First, I imported drivers for the servos and Opencv face recognition.
I chose Opencv because it is one of the fastest, I also considered using retinaface but the preformance cost was too high.


![face_detection_import](https://github.com/aizej/Automatic-face-targeting-laser-turret/assets/61479273/64cda7e4-ec08-4c12-84fe-25a316c2f530)


Then we set some variables for our hardware such as camera resolution or pins for our servos.

![hardware_setup](https://github.com/aizej/Automatic-face-targeting-laser-turret/assets/61479273/2c35f9dc-2733-401e-abb1-5e4beed84fa2)

After that, it is really important to get the angle of FOV of our camera and its cuttof(it only shows about 74.6% of horizontal image because of the set resolution)

![hardware_specs_for_calculations](https://github.com/aizej/Automatic-face-targeting-laser-turret/assets/61479273/53b998a5-14d6-469b-84b1-12b41d78f02a)

Then there is our function that calculates to what angle each servo should move from where the face is on the image and what real-life offsets it has defined.
This function takes in two numbers for x and y from 0 to 1 as. This represents where on the picture the face is [1,1] = bottom right [1,0] = up, right [0.5,0.5] = in the middle

![angle_2d_function](https://github.com/aizej/Automatic-face-targeting-laser-turret/assets/61479273/8cf2725a-0382-4434-a1e7-a5a68043677b)


Then we just setup loop where we take picture from the camera run it trough the face detection get middle of our detected face and pass it to the function.
Next step is just to pass output from our function to the servos.

![live_if_statemaent](https://github.com/aizej/Automatic-face-targeting-laser-turret/assets/61479273/40b665f3-144f-444a-ae59-bfd1b896dcfb)






