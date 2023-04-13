import serial
import time
arduino = serial.Serial(port='/dev/cu.usbserial-0001', baudrate=115200, timeout=.1)
def write_read(x):
    arduino.write(bytes(x, 'utf-8'))
    time.sleep(0.05)
    data = arduino.readline()
    return data
while True:
    num = input("Enter a number: ") # Taking input from user
    value = write_read(num)
    print("sending [" + str(value) + "] to esp288" ) # printing the value