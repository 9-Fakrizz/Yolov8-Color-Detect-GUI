import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext
import cv2
import pandas as pd
from ultralytics import YOLO
import cvzone
import threading
import os
import serial
from colorama import Fore
from geopy.distance import geodesic

polygon = [
    (13.8197316667, 100.5150371667),
    (13.8197428333, 100.5150236667),
    (13.8197716667, 100.5150546667),
    (13.8197738333, 100.5150331667),]

square_x = 87
square_y = 10
square_size = 415

model = YOLO('E:\My FakRizz StudiO\Download07\V8 GUI\colorv8.2.pt')

center_point = []
precenter_x = 0
precenter_y = 0

ser = None
cap = None
is_detecting = False
data = []

def split_data(data):
    for i in data:
        print(i[0], i[1])
        save_to_file(i[0], i[1])
    print(Fore.GREEN + "Data saved to file")

def check_and_clear_file(file_path):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        open(file_path, "w").close()

def is_inside_square(x, y):
    return square_x <= x <= square_x + square_size and square_y <= y <= square_y + square_size

def save_to_file(distance_x_cm, distance_y_cm, c="",path0 = "E:\My FakRizz StudiO\Download07\V8 GUI\log.txt"):
    with open(path0, "a") as file:
        file.write(f"{distance_x_cm:.2f} {distance_y_cm:.2f} {c},\n")
    log_message(f"Data saved to file: {distance_x_cm:.2f}, {distance_y_cm:.2f}")

def read_and_send_to_arduino(file_path, serial_port):
    with open(file_path, "r") as file:
        lines = file.readlines()
    log_message("Sending data to Arduino...")
    for line in lines:
        text = '#' + line.rstrip(',') + ';' + '\n'
        print(text)
        # serial_port.write(text.encode())
    log_message("Data sent to Arduino")

def start_detection_thread():
    detection_thread = threading.Thread(target=start_detection)
    detection_thread.start()

def stop_detection():
    global is_detecting
    is_detecting = False
    log_message("Detection stopped")

def start_detection_auto_thread():
    detection_thread = threading.Thread(target=start_detection_auto)
    detection_thread.start()

def save_data():
    if data:
        for d in data:
            save_to_file(d[0], d[1], d[2])
        print(Fore.GREEN + "Data saved to file")
        messagebox.showinfo("Information", "Data saved to file")
    else:
        messagebox.showwarning("Warning", "No data to save")

def clear_data():
    check_and_clear_file("E:\My FakRizz StudiO\Download07\V8 GUI\log.txt")
    log_message("Data cleared from file")
    # messagebox.showinfo("Information", "Data cleared from file")

def send_data():
    read_and_send_to_arduino("E:\My FakRizz StudiO\Download07\V8 GUI\log.txt", ser)
    check_and_clear_file("E:\My FakRizz StudiO\Download07\V8 GUI\log.txt")
    log_message("Data sent to Arduino")
    # messagebox.showinfo("Information", "Data sent to Arduino")

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

def start_detection():
    global cap, ser, is_detecting, precenter_x, precenter_y, center_point, data
    is_detecting = True
    log_message("Starting detection...")

    # ser = serial.Serial('COM5', 9600)
    cap = cv2.VideoCapture(0)

    check_and_clear_file("E:\My FakRizz StudiO\Download07\V8 GUI\log.txt")
    log_message("Cleared previous data from file")

    my_file = open("E:\My FakRizz StudiO\Download07\V8 GUI\cocoforv8.txt", "r")
    class_list = my_file.read().split("\n")

    count = 0
    data = []

    while is_detecting:

        '''line = ser2.readline().decode().strip()
            
            if line.startswith('$GPRMC'):  # ตรวจสอบว่าเป็นข้อมูล GPRMC หรือไม่
                data = line.split(',')
                
                if len(data) >= 4:
                    latitude = float(data[3][:2]) + float(data[3][2:]) / 60
                    longitude = float(data[5][:3]) + float(data[5][3:]) / 60
                    #print(f'Latitude: {latitude}, Longitude: {longitude}')

                    if point_inside_polygon(latitude, longitude, polygon):
                        inarea == 1
                        log_message("Point is in working area")
                    else:
                        print('ไม่อยู่ในพิกัดที่กำหนด')
                        log_message("Point is out of Area !!")
                        inarea == 0'''

        ret, frame = cap.read()
        if not ret:
            break

        count += 1
        if count % 5 != 0:
            continue

        frame = cv2.resize(frame, (600, 400))
        results = model.predict(frame)
        if(results):
            a = results[0].boxes.data
            px = pd.DataFrame(a).astype("float")

            for index, row in px.iterrows():
                x1 = int(row[0])
                y1 = int(row[1])
                x2 = int(row[2])
                y2 = int(row[3])
                d = int(row[5])
                
                if d < len(class_list):
                    c = class_list[d]
                    log_message(f"class ID is {c}")
                    print(f"class ID is {c}")
                else:
                    log_message(f"Invalid class ID {d}")
                    print(f"Invalid class ID {d}")  # Debugging statement
                    continue

                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)

                if center_x != precenter_x or center_y != precenter_y:
                    precenter_x = center_x
                    precenter_y = center_y

                    if is_inside_square(center_x, center_y):
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (100, 0, 100), 1)
                        cv2.circle(frame, (center_x, center_y), 3, (0, 0, 255), -1)
                        cvzone.putTextRect(frame, f'{c}', (x1, y1), 0.6, 1)

                        distance_x_cm = (-4E-06 * center_x ** 2 + 0.0408 * center_x - 3.1945) + 0.4
                        distance_y_cm = (2E-06 * center_y ** 2 - 0.0452 * center_y + 17.705) + 1.5

                        data.append([round(distance_x_cm, 2), round(distance_y_cm, 2), c])
                        if len(data) > len(px):
                            data.pop()

        cv2.imshow("Weed detect", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
             break
        

    # ser.close()
    cap.release()
    cv2.destroyAllWindows()
    log_message("Detection stopped and resources released")

def start_detection_auto():
    global cap, ser, is_detecting, precenter_x, precenter_y, center_point, data
    is_detecting = True
    log_message("Starting auto detection...")

    # ser = serial.Serial('COM5', 9600)
    cap = cv2.VideoCapture(0)

    check_and_clear_file("E:\My FakRizz StudiO\Download07\V8 GUI\log.txt")
    check_and_clear_file("E:\My FakRizz StudiO\Download07\V8 GUI\log_auto.txt")
    log_message("Cleared previous auto detection data from file")

    my_file = open("E:\My FakRizz StudiO\Download07\V8 GUI\cocoforv8.txt", "r")
    class_list = my_file.read().split("\n")

    count = 0
    data = []

    while is_detecting:

        '''line = ser2.readline().decode().strip()
            
            if line.startswith('$GPRMC'):  # ตรวจสอบว่าเป็นข้อมูล GPRMC หรือไม่
                data = line.split(',')
                
                if len(data) >= 4:
                    latitude = float(data[3][:2]) + float(data[3][2:]) / 60
                    longitude = float(data[5][:3]) + float(data[5][3:]) / 60
                    #print(f'Latitude: {latitude}, Longitude: {longitude}')

                    if point_inside_polygon(latitude, longitude, polygon):
                        inarea == 1
                        log_message("Point is in working area")
                    else:
                        print('ไม่อยู่ในพิกัดที่กำหนด')
                        log_message("Point is out of Area !!")
                        inarea == 0'''

        ret, frame = cap.read()
        if not ret:
            break

        count += 1
        if count % 5 != 0:
            continue

        frame = cv2.resize(frame, (600, 400))
        results = model.predict(frame)
        if results:
            a = results[0].boxes.data
            px = pd.DataFrame(a).astype("float")

            for index, row in px.iterrows():
                x1 = int(row[0])
                y1 = int(row[1])
                x2 = int(row[2])
                y2 = int(row[3])
                d = int(row[5])
                
                if d < len(class_list):
                    c = class_list[d]
                    log_message(f"class ID is {c}")
                    print(f"class ID is {c}")
                else:
                    log_message(f"Invalid class ID {d}")
                    print(f"Invalid class ID {d}")  # Debugging statement
                    continue

                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)

                if center_x != precenter_x or center_y != precenter_y:
                    precenter_x = center_x
                    precenter_y = center_y

                    if is_inside_square(center_x, center_y):
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (100, 0, 100), 1)
                        cv2.circle(frame, (center_x, center_y), 3, (0, 0, 255), -1)
                        cvzone.putTextRect(frame, f'{c}', (x1, y1), 0.6, 1)

                        distance_x_cm = (-4E-06 * center_x ** 2 + 0.0408 * center_x - 3.1945) + 0.4
                        distance_y_cm = (2E-06 * center_y ** 2 - 0.0452 * center_y + 17.705) + 1.5
                        
                        if c != "red" :
                            data.append([round(distance_x_cm, 2), round(distance_y_cm, 2), c])
                            if len(data) > len(px):
                                data.pop()

                        if count % (10 * 5) == 0:  # Every 20 seconds (since detection is done every 5 frames)
                            path1 = "E:\My FakRizz StudiO\Download07\V8 GUI\log_auto.txt"
                            if data:
                                for d in data:
                                    save_to_file(d[0], d[1], d[2])
                                    save_to_file(d[0], d[1], d[2],path1)
                                    print(Fore.GREEN + "Data saved to file")

                            send_data()
                            count = 0

                        # new_data = [round(distance_x_cm, 2), round(distance_y_cm, 2),c]
                        # if new_data not in data:
                        #     data.append(new_data)
                        #     save_to_file(new_data[0], new_data[1], c)

        cv2.imshow("Weed detect", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


    # ser.close()
    cap.release()
    cv2.destroyAllWindows()
    log_message("Auto detection stopped and resources released")

def log_message(message):
    text_box.insert(tk.END, message + '\n')
    text_box.see(tk.END)  # Scroll to the end

def clear_log():
    text_box.delete(1.0, tk.END)

def stop_code():
    root.destroy()


# GUI setup
root = tk.Tk()
root.title("Detection GUI")
root.geometry("380x380")

# Create and place the buttons using place
start_button = tk.Button(root, text="Start Detection", command=start_detection_thread)
start_button.place(x=50, y=50, width=120, height=30)

auto_detect_button = tk.Button(root, text="Auto Detection", command=start_detection_auto_thread)
auto_detect_button.place(x=200, y=50, width=120, height=30)

stop_button = tk.Button(root, text="Stop Detection", command=stop_detection)
stop_button.place(x=50, y=100, width=120, height=30)

save_button = tk.Button(root, text="Save Data", command=save_data)
save_button.place(x=200, y=100, width=120, height=30)

clear_button = tk.Button(root, text="Clear Data", command=clear_data)
clear_button.place(x=50, y=150, width=120, height=30)

send_button = tk.Button(root, text="Send Data to Arduino", command=send_data)
send_button.place(x=200, y=150, width=120, height=30)

# Create a text box for logs
text_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=35, height=6)
text_box.grid(row=10, column=0, columnspan=2, padx=20, pady=10)
text_box.place(x=50, y=200)

# Add the clear log button
clear_log_button = tk.Button(root, text="Clear Log", command=clear_log)
clear_log_button.place(x=125, y=320, width=120, height=30)

exit_button = tk.Button(root, text="Exit", command=stop_code)
exit_button.place(x=320, y=320, width=120, height=30)
exit_button.pack()

root.mainloop()
