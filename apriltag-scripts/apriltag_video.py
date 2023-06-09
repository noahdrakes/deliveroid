#!/usr/bin/env python

#modules for apriltag methods
from argparse import ArgumentParser
import os
import cv2
import apriltag
import numpy
import math

#modules for serial data transfer
import serial
import time

# GLOBALS
robotPositionedCorrectlySTATE   = 1
ROBOTNOTFACINGDESTINATION       = 1
ROBOTFACINGDESTINATION          = 2

robotCommandInProgress          = 3
WAITINGFORCOMMAND               = 3
COMMANDINPROGRESS               = 4

robotReturnToOrigin             = 5
ROBOTNOTRETURNING               = 5
ROBOTRETURNINGTOORIGIN          = 6  

ROBOTEXITPROGRAMFLAG            = 0

# variable for path to serial port
arduino = ""

################################################################################
def initializeSerialDataTransfer():
    global arduino
    arduino = serial.Serial(port='/dev/cu.usbserial-0001', baudrate=115200, timeout=.1)

def transmitRobotStateToWifiModule():
    global arduino
    state = str(returnRobotPositionedCorrectlyState()) + str(returnRobotCommandInProgress()) + str(returnRobotReturnToOrigin())
    # state = input("input a 3 digit number")
    arduino.write(bytes(state, 'utf-8'))
    time.sleep(0.05)

# RETURN METHODS
def returnExitProgramFlag():
    global ROBOTEXITPROGRAMFLAG
    return ROBOTEXITPROGRAMFLAG

def returnRobotPositionedCorrectlyState():
    global robotPositionedCorrectlySTATE
    return robotPositionedCorrectlySTATE

def returnRobotCommandInProgress():
    global robotCommandInProgress
    return robotCommandInProgress

def returnRobotReturnToOrigin():
    global robotReturnToOrigin
    return robotReturnToOrigin


# UPDATE METHODS
def updateExitProgramFlag(state):
    global ROBOTEXITPROGRAMFLAG
    ROBOTEXITPROGRAMFLAG = state

def updateRobotPositionedCorrectlyState(state):
    global robotPositionedCorrectlySTATE
    robotPositionedCorrectlySTATE = state
    transmitRobotStateToWifiModule()

def updateRobotCommandInProgress(state):
    global robotCommandInProgress
    robotCommandInProgress = state
    transmitRobotStateToWifiModule()

def updateRobotReturnToOrigin(state):
    global robotReturnToOrigin
    robotReturnToOrigin = state
    transmitRobotStateToWifiModule()

#########################################


def apriltag_video(input_streams=['../media/input/single_tag.mp4', '../media/input/multiple_tags.mp4'], # For default cam use -> [0]
                   output_stream=False,
                   display_stream=True,
                   detection_window_name='AprilTag',
                  ):

    '''
    Detect AprilTags from video stream.

    Args:   input_streams [list(int/str)]: Camera index or movie name to run detection algorithm on
            output_stream [bool]: Boolean flag to save/not stream annotated with detections
            display_stream [bool]: Boolean flag to display/not stream annotated with detections
            detection_window_name [str]: Title of displayed (output) tag detection window
    '''

    parser = ArgumentParser(description='Detect AprilTags from video stream.')
    apriltag.add_arguments(parser)
    options = parser.parse_args()

    '''
    Set up a reasonable search path for the apriltag DLL.
    Either install the DLL in the appropriate system-wide
    location, or specify your own search paths as needed.
    '''


    detector = apriltag.Detector(options, searchpath=apriltag._get_dll_path())

    for stream in input_streams:
        

        video = cv2.VideoCapture(0)

        output = None

        if output_stream:
            width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(video.get(cv2.CAP_PROP_FPS))
            codec = cv2.VideoWriter_fourcc(*'XVID')
            if type(stream) != int:
                output_path = '../media/output/'+str(os.path.split(stream)[1])
                output_path = output_path.replace(str(os.path.splitext(stream)[1]), '.avi')
            else:
                output_path = '../media/output/'+'camera_'+str(stream)+'.avi'
            output = cv2.VideoWriter(output_path, codec, fps, (width, height))


        transmitRobotStateToWifiModule()    
        while(1): 
            if returnExitProgramFlag() == 1:
                break

            # IF ROBOT IS NOT RETURNING TO ORIGIN AND IS AWAITING  COMMAND, THEN HAVE THE USER 
            # INPUT DESTINATION COORDINATES
            if (returnRobotReturnToOrigin() == ROBOTNOTRETURNING and returnRobotCommandInProgress() == WAITINGFORCOMMAND):
                destCoord = [0 , 0]
                destCoord[0] = int(input("ENTER X COORDINATE FOR DESTINATION: "))
                destCoord[1] = int(input("ENTER Y COORDINATE FOR DESTINATION: "))
                updateRobotCommandInProgress(4)
                

            # ELSE THE ROBOT IS RETURNING TO ORIGIN SO THE DESTINATION COORDINATES HAVE TO BE SET TO ORIGIN
            # set to 50 so point is visible on screen
            else:
                destCoord[0] = 50
                destCoord[1] = 50
                updateRobotReturnToOrigin(ROBOTRETURNINGTOORIGIN)

            while(returnRobotCommandInProgress() == COMMANDINPROGRESS):

                success, frame = video.read()
                if not success:
                    break
                robotCoordinates, poseMatrix1, poseMatrix2, overlay = apriltag.detect_tags(frame,
                                                    detector,
                                                    camera_params= (1094.285869, 1110.03366, 586.92316, 306.77308),
                                                    tag_size=0.0762,
                                                    vizualization=3,
                                                    verbose=3,
                                                    annotation=True)

                # coordinate array flag is asserted when april tag is detected and robotCoordinate array fills up
                coordinate_array_flag = numpy.any(robotCoordinates)

                # only prints if coordinate array is filled (if apriltag is detected)
                if (coordinate_array_flag != False):
                    
                    # calculating absolute robot angle
                    if poseMatrix2[0] >=0:
                        robotAngle =  (numpy.arccos(poseMatrix1[0]) / math.pi) * 180
                    else:
                        robotAngle =  (numpy.arccos(poseMatrix1[0]) / math.pi) * -180
                    
                    # TRANSPOSED COORDINATES    
                    # we need to transpose the robot coordinates and destination coordinates to be positioned as if
                    # the robot is at the origin. This is to make it easier to calculate the angle between two vectors.
                    destCoordTransposed = [(destCoord[0] - robotCoordinates[0]), (destCoord[1] - robotCoordinates[1])]

                    transposedRobotCoordinates = [0, 0]
                    
                    destinationAngleFromXAxis = 180 / math.pi * numpy.arctan(destCoordTransposed[1]/destCoordTransposed[0])


                    destinationAngle = 0

                    # variable name change for easier read
                    destX = destCoordTransposed[0]
                    destY = destCoordTransposed[1]


                    # CHECK "APRILTAG ANGLE CASES.JPG" to understand math

                    # case 1
                    if (destX>0 and (destY)>0):
                        destinationAngle = destinationAngleFromXAxis
                    
                    # case 2
                    elif (destX<0 and destY>0):
                        destinationAngleFromXAxis = 180 / math.pi * numpy.arctan(abs(destCoordTransposed[1])/abs(destCoordTransposed[0]))
                        destinationAngle = 180 - destinationAngleFromXAxis
                    
                    # case 3
                    elif (destX<0 and destY<0):
                        destinationAngleFromXAxis = 180 / math.pi * numpy.arctan((destCoordTransposed[1])/(destCoordTransposed[0]))
                        destinationAngle = -1 * (180 - destinationAngleFromXAxis)

                    # case 4
                    elif (destX > 0 and destY < 0):
                        destinationAngleFromXAxis = 180 / math.pi * numpy.arctan((destCoordTransposed[1])/(destCoordTransposed[0]))
                        destinationAngle = destinationAngleFromXAxis

                    # how close the robot angle to pointing directly at destination address
                    differenceAngle = destinationAngle - robotAngle

                    if (differenceAngle > -5 and differenceAngle < 5):
                        updateRobotPositionedCorrectlyState(ROBOTFACINGDESTINATION)
                    else:
                        updateRobotPositionedCorrectlyState(ROBOTNOTFACINGDESTINATION)

                    

                    # calculate how close the robot is to the destination
                    robotDistancefromDestination = destCoord[0] - robotCoordinates[0], destCoord[1] - robotCoordinates[1]

                    if (robotDistancefromDestination[0] > -100 and robotDistancefromDestination[0] < 100):
                        if (robotDistancefromDestination[1] > -100 and robotDistancefromDestination[1] < 100):
                            if (returnRobotCommandInProgress() == COMMANDINPROGRESS) and returnRobotReturnToOrigin() == ROBOTNOTRETURNING:
                                updateRobotReturnToOrigin(ROBOTRETURNINGTOORIGIN)
                                print("ROBOT RETURNING TO ORIGIN, ", returnRobotReturnToOrigin())
                                break
                            else:
                                updateRobotReturnToOrigin(ROBOTNOTRETURNING)
                                updateRobotCommandInProgress(WAITINGFORCOMMAND)
                                break

                    print("\r robot position: ",robotCoordinates)
                    print("\r robot distance from destination: ", robotDistancefromDestination)
                    print("\r destination coordinate: ", destCoord)
                    print("\r robot angle: ", robotAngle)
                    print("\r destination angle from x axis: ", destinationAngleFromXAxis)
                    print("\r destination angle: ", differenceAngle)

                if output_stream:
                    output.write(overlay)

                # because the image is flipped the Y destination point needs to be corrected
                yErrorResolution = 1100

                if display_stream:

                    # flipping the image so that our coordinate systems starts at bottom left of camera
                    overlay = cv2.flip(overlay, 0)

                    # displaying destination coordinate as a red circle
                    overlay = cv2.circle(overlay, (destCoord[0], yErrorResolution - destCoord[1]), radius=15, color=(0, 0, 255), thickness=-1)
                    cv2.imshow(detection_window_name, overlay)
                    
                    if cv2.waitKey(1) & 0xFF == ord(' '): # Press space bar to terminate
                        updateExitProgramFlag(1)
                        break

################################################################################

if __name__ == '__main__':
    initializeSerialDataTransfer()
    apriltag_video()
    
    