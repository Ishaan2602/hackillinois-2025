from picarx import Picarx
from time import sleep
from vilib import Vilib
from robot_hat import Music, TTS
import math
from os import geteuid

if geteuid() != 0:
    print(f"\033[0;33m{'The program needs to be run using sudo, otherwise there may be no sound.'}\033[0m")

# Initialize Picarx and other components
px = Picarx()
music = Music()
tts = TTS()

# Set volume and language for TTS
music.music_set_volume(1000000)
tts.lang("en-US")

# Constants for obstacle avoidance
POWER = 50
SafeDistance = 40  # > 40 safe
DangerDistance = 20  # > 20 && < 40 turn around, < 20 backward

# Constants for pose tracking
CAMERA_PAN_RANGE = (-45, 45)  # Pan angle range (left to right)
CAMERA_TILT_RANGE = (-35, 35)  # Tilt angle range (down to up)
SCAN_SPEED = 5  # Degrees to move per step
FACE_CENTER_X = 320  # Center X coordinate of the camera frame (640x480 resolution)
FACE_CENTER_Y = 240  # Center Y coordinate of the camera frame
MIN_JOINTS = 5  # Minimum number of joints to detect a person

def clamp_number(num, a, b):
    return max(min(num, max(a, b)), min(a, b))

def calculate_steering_angle(delta_x, distance):
    """
    Calculate the steering angle (theta) based on delta_x and distance.
    Formula: theta = arctan(delta_x / distance)
    """
    if distance == 0:  # Avoid division by zero
        return 0
    theta_radians = math.atan2(delta_x, distance)  # Use atan2 for better handling of quadrants
    theta_degrees = math.degrees(theta_radians)  # Convert radians to degrees
    return theta_degrees

def scan_for_person():
    # Start the camera and enable pose detection
    Vilib.camera_start(vflip=False, hflip=False)
    Vilib.display(local=True, web=True)
    Vilib.pose_detect_switch(True)
    sleep(1)  # Allow time for initialization

    pan_angle = 0  # Initial pan angle (centered)
    tilt_angle = 30  # Initial tilt angle (45 degrees inclined) CHANGE!
    pan_direction = 1  # 1 for right, -1 for left

    # Set the initial camera angles
    px.set_cam_pan_angle(pan_angle)
    px.set_cam_tilt_angle(tilt_angle)

    while True:
        # Move the camera in a horizontal scanning pattern
        pan_angle += SCAN_SPEED * pan_direction

        # Clamp the pan angle to the valid range
        pan_angle = clamp_number(pan_angle, CAMERA_PAN_RANGE[0], CAMERA_PAN_RANGE[1])

        # Set the pan angle (tilt angle remains fixed at 45 degrees)
        px.set_cam_pan_angle(pan_angle)

        # Check if a person is detected (at least MIN_JOINTS joints)
        if Vilib.detect_obj_parameter['body_joints'] != 0:  # If a body is detected
            joints = Vilib.detect_obj_parameter['body_joints']
            if len(joints) >= MIN_JOINTS:  # If at least MIN_JOINTS joints are detected
                print("Person detected! Stopping scan.")
                return True # Exit the scan function

        # Reverse direction if the limits are reached
        if pan_angle >= CAMERA_PAN_RANGE[1] or pan_angle <= CAMERA_PAN_RANGE[0]:
            pan_direction *= -1

        sleep(0.1)  # Small delay for smooth movement

def track_person():
    obs_distance = 100
    #while distance > 1:
    while True:
        obs_distance = px.ultrasonic.read()
        print("this is distance")
        print(obs_distance)
        if (obs_distance < 0): 
            obs_distance = 200
        if obs_distance < 40: #and distance >= DangerDistance:
            return True 
            break
        if Vilib.detect_obj_parameter['body_joints'] != 0:  # If a body is detected
            joints = Vilib.detect_obj_parameter['body_joints']
            if len(joints) >= MIN_JOINTS:  # If at least MIN_JOINTS joints are detected
                # Output all joint values
                 #print("Joint Values:")
                 #for i, joint in enumerate(joints):
                     #print(f"Joint {i}: (x={joint[0]}, y={joint[1],}, z = {joint[2]})")

                # Get the center of the detected person
                x = sum(joint[0] for joint in joints) / len(joints) * 640 # Average X coordinate
                y = sum(joint[1] for joint in joints) / len(joints) * 480
                z = sum(joint[2] for joint in joints) / len(joints) * 10

                if obs_distance < 80:
                    px.set_cam_tilt_angle(40)

                # 0 # Average Y coordinate

                # Output the average x value
                # print(f"Average X Value: {x}")

                # Output the average z value
                print(f"Average Z Value: {z}")

                # Calculate the difference between the person's position and the center of the frame
                delta_x = x - FACE_CENTER_X
                delta_y = y - FACE_CENTER_Y



                # Get the distance to the person from the ultrasonic sensor
                #distance = px.ultrasonic.read()
                distance = z

                # Calculate the steering angle using the formula
                if (abs(delta_x) > 60):
                    steering_angle = calculate_steering_angle(delta_x, distance)
                else:
                    steering_angle = 0
                # print(f"Delta X: {delta_x}, Distance: {distance}, Steering Angle: {steering_angle}")

                # Clamp the steering angle to the valid range
                #steering_angle = clamp_number(steering_angle, -60, 60) #changed range here
                print(steering_angle)

                # Set the steering angle and move forward
                px.set_dir_servo_angle(steering_angle)
                px.forward(POWER)
                #px.set_motor_speed(2,-2.16*POWER)

                sleep(0.05)  # Small delay for smooth movement
            else:
                px.forward(0)  # Stop if not enough joints are detected
                sleep(0.02)
        else:
            px.forward(0)  # Stop if no person is detected
            sleep(0.02)
    #print(f"The distance is.... {distance}")
    #return distance

def avoid_obstacle():
    distance = px.ultrasonic.read()  # Read distance from ultrasonic sensor
    print("Distance: ", distance)

    if distance >= SafeDistance:  # If safe, move forward
        px.set_dir_servo_angle(0)
        px.forward(POWER)
        #px.set_motor_speed(2,-2.16*POWER)
    elif distance >= DangerDistance:  # If close, turn and move forward
        px.set_dir_servo_angle(30)
        px.forward(POWER)
        #px.set_motor_speed(2,-2.16*POWER)
        sleep(0.1)
    else:  # If too close, move backward
        px.set_dir_servo_angle(-30)
        px.backward(POWER)
        #px.set_motor_speed(2,2.16*POWER)
        sleep(0.5)

def play_advertisement():
    print('Playing Music') 
    # music.music_play('../musics/slow-trail-Ahjay_Stelino.mp3')
    music.music_play('/John-Deere.mp3')
    sleep(30)
    music.music_stop()
    words = "Welcome Welcome, introducing our BRAND new product at a 20% discount for a limited time!"
    print(f'{words}')
    tts.say(words)
    sleep(1)
    tts.lang("fr-FR")
    tts.say(words)
    sleep(1)
    tts.lang("es-ES")
    tts.say(words)
    sleep(1)

def main():
    try:
        # Start scanning for a person
        check1 = scan_for_person()

        # Once a person is detected, track them and avoid obstacles
        while check1:
            #distance = track_person()
            check2 = track_person()
            #avoid_obstacle()

            # If close enough to the person, stop and play advertisement
            #distance = px.ultrasonic.read()
            #if distance < SafeDistance and distance >= DangerDistance: #might change of distance < DangerDistance
            sleep(1)
            if check2:
                px.forward(0)  # Stop the bot
                play_advertisement()  # Play the advertisement
            break  # Exit the loop after playing the advertisement

    finally:
        px.stop()  # Stop the bot
        Vilib.camera_close()  # Close the camera
        print("Stop and exit")
        sleep(0.1)

if __name__ == "__main__":
    main()
    