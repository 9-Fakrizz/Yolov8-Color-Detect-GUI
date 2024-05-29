import cv2
from ultralytics import YOLO
import cvzone
import numpy as np
import time
import keyboard
from colorama import Fore
import os
import serial
from geopy.distance import geodesic

import pandas as pd
from openpyxl import load_workbook
from datetime import datetime

square_x =105
square_y = 21
square_size = 415

#model = YOLO('D:/phyton/project laser/New folder/kanaL.pt')
model = YOLO('D:/phyton/project laser/New folder/colorv8.2.pt')

center_point = []
precenter_x = 0
precenter_y = 0

# เส้นทางที่กำหนด
polygon = [
    (13.819778166666667,100.51505666666667),
    (13.819782666666667, 100.51504),
    (13.8197425,100.5150416),
    (13.819751,100.5150273),
]
def split_data(data):
    for i in data:
        print(i[0] , i[1])
        save_to_file(i[0], i[1])
    print(Fore.GREEN + "Data saved to file")


def check_and_clear_file(file_path):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        open(file_path, "w").close()

def is_inside_square(x, y):
    return square_x <= x <= square_x + square_size and square_y <= y <= square_y + square_size


def save_to_file(distance_x_cm, distance_y_cm, c):
    if c != "kana":  #whe detect object that is not save to file
        with open("D:/phyton/project laser/distance_data.txt", "a") as file:
            file.write(f"{distance_x_cm:.2f} {distance_y_cm:.2f},")


def read_and_send_to_arduino(file_path, serial_port):
    with open(file_path, "r") as file:
        lines = file.readlines()
    print("*********************************************************************")
    for line in lines:
        text = '#'+ line.rstrip(',') + ';'+ '\n'
        print(text)
        serial_port.write(text.encode())
        
def JRTRGB(event, x, y, flags, param):
    global center_point
    if event == cv2.EVENT_MOUSEMOVE:
        center_point = [x, y]
        print(f"Center Point Coordinates: {center_point}")
        text = f"({x}, {y})"
        cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 1)

# Check and clear the file before starting
check_and_clear_file("D:/phyton/project laser/distance_data.txt")

cv2.namedWindow('JRT')
cv2.setMouseCallback('JRT', JRTRGB)

cap = cv2.VideoCapture(0)                                                             
my_file = open("D:/phyton/project laser/cocoforv8.txt", "r")
data = my_file.read()
class_list = data.split("\n")

count = 0
data_count = 0
MAX_DATA_COUNT = 5

ser = serial.Serial('COM5', 115200) #arduino  

inarea =0

def point_inside_polygon(x, y, poly):
    n = len(poly)
    inside = False

    p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside

#ser2 = serial.Serial('COM12', 9600)  # RTK

while True:
    '''line = ser2.readline().decode().strip()
    
    if line.startswith('$GPRMC'):  # ตรวจสอบว่าเป็นข้อมูล GPRMC หรือไม่
        data = line.split(',')
        
        if len(data) >= 4:
            latitude = float(data[3][:2]) + float(data[3][2:]) / 60
            longitude = float(data[5][:3]) + float(data[5][3:]) / 60
            #print(f'Latitude: {latitude}, Longitude: {longitude}')

            if point_inside_polygon(latitude, longitude, polygon):
                inarea == 1
            else:
                print('ไม่อยู่ในพิกัดที่กำหนด')
                inarea == 0'''
        
    ret, frame = cap.read()
    if not ret :
        break

    count += 1
    if count % 5 != 0:
        continue

    frame = cv2.resize(frame, (600, 400))
    results = model.predict(frame)
    a = results[0].boxes.data
    px = pd.DataFrame(a).astype("float")

    for index, row in px.iterrows():
        x1 = int(row[0])
        y1 = int(row[1])
        x2 = int(row[2])
        y2 = int(row[3])
        d = int(row[5])
        c = class_list[d]

        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)

        if center_x != precenter_x or center_y != precenter_y:
            precenter_x = center_x
            precenter_y = center_y

            if is_inside_square(center_x, center_y) :
                cv2.rectangle(frame, (x1, y1), (x2, y2), (100, 0, 100), 1)
                cv2.circle(frame, (center_x, center_y), 3, (0, 0, 255), -1)
                cvzone.putTextRect(frame, f'{c}', (x1, y1), 0.6, 1)

                print(Fore.BLUE +'point of:', c)
                print(Fore.CYAN +'center_point= x:', center_x, )
                print(Fore.YELLOW +'center_point= y:', center_y)

                #distance_x_cm = ((center_x * 29.4) / 600)
                #distance_y_cm = ((center_y * 24.5) / 400)
                
                distance_x_cm =-2E-06*center_x**2 + 0.049*center_x - 6.1508
                distance_y_cm =2E-06*center_y**2 - 0.0547*center_y + 21.026

                print(Fore.RED + f'Conversion from pixels to cm: {distance_x_cm:.2f} cm, {distance_y_cm:.2f} cm')

                if keyboard.is_pressed('s'):                                                          
                    save_to_file(distance_x_cm, distance_y_cm,c)
                    print(Fore.GREEN + "Data saved to file")

                if keyboard.is_pressed('c'):                                                          
                    check_and_clear_file("D:/phyton/project laser/distance_data.txt")
                    print(Fore.RED + "Data cleared from file")

                if keyboard.is_pressed('a'):
                    print(Fore.GREEN + "A action")
                    if abs(distance_x_cm - distance_y_cm) / abs(distance_x_cm + distance_y_cm) <= 0.98:
                        save_to_file(distance_x_cm, distance_y_cm,c)
                        print(Fore.GREEN + "Data saved to file")
                        data_count += 1  

                    if data_count >= MAX_DATA_COUNT:
                        read_and_send_to_arduino("D:/phyton/project laser/distance_data.txt", ser)
                        check_and_clear_file("D:/phyton/project laser/distance_data.txt")
                        print(Fore.MAGENTA + "Data sent to Arduino")
                        data_count = 0
                    else:
                         print(Fore.YELLOW + "Data not saved due to significant difference between distances")
            
    if keyboard.is_pressed('p'):                                                              
        read_and_send_to_arduino("D:/phyton/project laser/distance_data.txt", ser)
        print(Fore.MAGENTA + "Data sent to Arduino")
        check_and_clear_file("D:/phyton/project laser/distance_data.txt")
          
            #cv2.rectangle(frame, (square_x, square_y), (square_x + square_size, square_y + square_size), (0, 180, 0), 2)
    cv2.imshow("JRT", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
                
# Close the serial port
ser.close()
cap.release()
cv2.destroyAllWindows()