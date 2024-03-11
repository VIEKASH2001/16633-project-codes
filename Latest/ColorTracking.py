#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/home/pi/MasterPi/')
import cv2
import time
import signal
import Camera
import argparse
import threading
import yaml_handle
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.PID as PID
import HiwonderSDK.Misc as Misc
import HiwonderSDK.Board as Board
import queue

# This queue will hold the received coordinates
coordinates_queue = queue.Queue()
object_detected = False
#### SOCKET COMM
import socket
def server_socket_thread():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 65432))
    server_socket.listen(1)
    print("Server socket listening for connections...")
    
    while True:
        client_socket, addr = server_socket.accept()
        print('Accepted connection from {}:{}'.format(addr[0], addr[1]))
        client_handler = threading.Thread(target=handle_client_connection,
                                          args=(client_socket,))
        client_handler.start()

# Start the server socket thread
threading.Thread(target=server_socket_thread).start()

def handle_client_connection(client_socket):
    try:
        while True:
            data = client_socket.recv(1024).decode()
            if not data:
                break
            # Parse the received coordinates
            center_x, center_y = map(int, data.split(','))
            # Put the coordinates into the queue
            coordinates_queue.put((center_x, center_y))
    finally:
        client_socket.close()


if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

AK = ArmIK()

range_rgb = {
    'red': (0, 0, 255),
    'blue': (255, 0, 0),
    'green': (0, 255, 0),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
}

lab_data = None
def load_config():
    global lab_data, servo_data
    
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)

__target_color = ('red',)
# 设置检测颜色
def setTargetColor(target_color):
    global __target_color

    print("COLOR", target_color)
    __target_color = target_color
    return (True, ())

# 找出面积最大的轮廓
# 参数为要比较的轮廓的列表
def getAreaMaxContour(contours):
    contour_area_temp = 0
    contour_area_max = 0
    areaMaxContour = None
    for c in contours:  # 历遍所有轮廓
        contour_area_temp = math.fabs(cv2.contourArea(c))  # 计算轮廓面积
        if contour_area_temp > contour_area_max:
            contour_area_max = contour_area_temp
            if contour_area_temp > 300:  # 只有在面积大于300时，最大面积的轮廓才是有效的，以过滤干扰
                areaMaxContour = c
    return areaMaxContour, contour_area_max  # 返回最大的轮廓

# 夹持器夹取时闭合的角度
servo1 = 1500

x_dis = 1500
y_dis = 860

x_pid = PID.PID(P=0.28, I=0.03, D=0.03)  # pid初始化
y_pid = PID.PID(P=0.28, I=0.03, D=0.03)

go_pid = PID.PID(P=0.28, I=0.1, D=0.05)
about_pid = PID.PID(P=0.35, I=0.08, D=0.005)

y_speed = 0
x_speed = 0

# 初始位置
def initMove():
    Board.setPWMServoPulse(1, servo1, 800)
    AK.setPitchRangeMoving((0, 8, 18), 0,-90, 90, 1500)

# 设置蜂鸣器
def setBuzzer(timer):
    Board.setBuzzer(0)
    Board.setBuzzer(1)
    time.sleep(timer)
    Board.setBuzzer(0)

# 关闭电机
def MotorStop():
    Board.setMotor(1, 0) 
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)

#设置扩展板的RGB灯颜色使其跟要追踪的颜色一致
def set_rgb(color):
    if color == "red":
        Board.RGB.setPixelColor(0, Board.PixelColor(255, 0, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(255, 0, 0))
        Board.RGB.show()
    elif color == "green":
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 255, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 255, 0))
        Board.RGB.show()
    elif color == "blue":
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 255))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 255))
        Board.RGB.show()
    else:
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
        Board.RGB.show()

_stop = False
__isRunning = False
detect_color = 'None'
start_pick_up = False
# 变量重置
def reset():
    global _stop
    global __isRunning
    global detect_color
    global start_pick_up
    global __target_color
    global x_dis,y_dis
    global enableWheel
    
    x_dis = 1500
    y_dis = 860
    x_pid.clear()
    y_pid.clear()
    go_pid.clear()
    about_pid.clear()
    _stop = False
    enableWheel = False
    __target_color = ()
    detect_color = 'None'
    start_pick_up = False

# app初始化调用
def init():
    print("ColorTracking Init")
    load_config()
    reset()
    initMove()

# app开始玩法调用
def start():
    global __isRunning
    reset()
    __isRunning = True
    print("ColorTracking Start")

# app停止玩法调用
def stop():
    global _stop 
    global __isRunning
    _stop = True
    reset()
    initMove()
    MotorStop()
    __isRunning = False
    set_rgb('None')
    print("ColorTracking Stop")

# app退出玩法调用
def exit():
    global _stop
    global __isRunning
    _stop = True
    reset()
    initMove()
    MotorStop()
    __isRunning = False
    set_rgb('None')
    print("ColorTracking Exit")

# 设置车身跟随函数
enableWheel = False
def setWheel(Wheel = 0,):
    global enableWheel
    if Wheel :
        enableWheel = True
        Board.setPWMServoPulse(1, 1500, 800)
        AK.setPitchRangeMoving((0, 7, 12), -50, -90, 0, 1500)
    else:
        enableWheel = False
        MotorStop()
        initMove()
    return (True, ())

rect = None
size = (640, 480)


def rotate_clockwise(speed):
    """
    Rotate the platform clockwise at a given speed.
    speed: A value indicating the speed and direction. Positive for clockwise, negative for counterclockwise.
    """
    speed_1 = speed
    speed_2 = -speed
    speed_3 = speed
    speed_4 = -speed
    
    # Assuming Board.setMotor(ID, speed) sets the speed of the motor (ID ranges from 1 to 4)
    Board.setMotor(1, speed_1)
    Board.setMotor(2, speed_2)
    Board.setMotor(3, speed_3)
    Board.setMotor(4, speed_4)

def rotate_counterclockwise(speed):
    """
    Rotate the platform counterclockwise at a given speed.
    speed: A value indicating the speed and direction. Positive for counterclockwise, negative for clockwise.
    """
    # Simply call rotate_clockwise with negative speed for counterclockwise rotation
    rotate_clockwise(-speed)


def wheel_control():         
    global rect
    global __isRunning
    global enableWheel
    global detect_color
    global start_pick_up
    global img_h, img_w
    global x_dis, y_dis
    global x_speed,y_speed
    global center_x, center_y

    if abs(center_x - img_w/2.0) < 15: # 移动幅度比较小，则不需要动
        about_pid.SetPoint = center_x
    else:
        about_pid.SetPoint = img_w/2.0 # 设定
    about_pid.update(center_x) # 当前
    x_speed = -int(about_pid.output)  # 获取PID输出值
    x_speed = -100 if x_speed < -100 else x_speed
    x_speed = 100 if x_speed > 100 else x_speed
    
    if abs(center_y - img_h/2.0) < 10: # 移动幅度比较小，则不需要动
        go_pid.SetPoint = center_y
    else:
        go_pid.SetPoint = img_h/2.0  
    go_pid.update(center_y)
    y_speed = int(go_pid.output)# 获取PID输出值
    y_speed = -100 if y_speed < -100 else y_speed
    y_speed = 100 if y_speed > 100 else y_speed
    speed_1 = int(y_speed + x_speed) # 速度合成
    speed_2 = int(y_speed - x_speed)
    speed_3 = int(y_speed - x_speed) 
    speed_4 = int(y_speed + x_speed)
    Board.setMotor(1, speed_1)
    Board.setMotor(2, speed_2)
    Board.setMotor(3, speed_3)
    Board.setMotor(4, speed_4)
    return
def run(img):
    global rect
    global __isRunning, object_detected
    global enableWheel
    global detect_color
    global start_pick_up
    global img_h, img_w
    global x_dis, y_dis
    global x_speed,y_speed
    global center_x, center_y
    center_x, center_y = 0,0
    img_h, img_w = img.shape[:2]
    Motor_ = True
    if not __isRunning:   # 检测是否开启玩法，没有开启则返回原图像
        MotorStop()
        return img
    speed = 30
    if not object_detected:
        rotate_clockwise(speed)
    while not coordinates_queue.empty():
        if not object_detected:
            object_detected = True  # Update the flag to indicate object detection
            MotorStop()  # Stop further movement
        Board.setMotor(1, speed)
        Board.setMotor(2, speed)
        Board.setMotor(3, speed)
        Board.setMotor(4, speed)
        coords_text = f"X: {center_x}, Y: {center_y}"
        cv2.putText(img, coords_text, (400, 400), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.circle(img, (center_x, center_y), 7, (0, 255, 0), -1)

        # if enableWheel == True:   #  检测是否开启车身跟随;   enableWheel = True,为开启车身跟随
        #     Motor_ = True               
        #     if abs(center_x - img_w/2.0) < 15: # 移动幅度比较小，则不需要动
        #         about_pid.SetPoint = center_x
        #     else:
        #         about_pid.SetPoint = img_w/2.0 # 设定
        #     about_pid.update(center_x) # 当前
        #     x_speed = -int(about_pid.output)  # 获取PID输出值
        #     x_speed = -100 if x_speed < -100 else x_speed
        #     x_speed = 100 if x_speed > 100 else x_speed
            
        #     if abs(center_y - img_h/2.0) < 10: # 移动幅度比较小，则不需要动
        #         go_pid.SetPoint = center_y
        #     else:
        #         go_pid.SetPoint = img_h/2.0  
        #     go_pid.update(center_y)
        #     y_speed = int(go_pid.output)# 获取PID输出值
        #     y_speed = -100 if y_speed < -100 else y_speed
        #     y_speed = 100 if y_speed > 100 else y_speed
        #     speed_1 = int(y_speed + x_speed) # 速度合成
        #     speed_2 = int(y_speed - x_speed)
        #     speed_3 = int(y_speed - x_speed) 
        #     speed_4 = int(y_speed + x_speed)
        #     Board.setMotor(1, speed_1)
        #     Board.setMotor(2, speed_2)
        #     Board.setMotor(3, speed_3)
        #     Board.setMotor(4, speed_4)
        # else:
        #     if Motor_:
        #         MotorStop()
        #         Motor_ = False
                
        #     x_pid.SetPoint = img_w / 2.0  # 设定
        #     x_pid.update(center_x)  # 当前
        #     dx = x_pid.output
        #     x_dis += int(dx)  # 输出
        #     x_dis = 500 if x_dis < 500 else x_dis
        #     x_dis = 2500 if x_dis > 2500 else x_dis
            
        #     y_pid.SetPoint = img_h / 2.0  # 设定
        #     y_pid.update(center_y)  # 当前
        #     dy = y_pid.output
        #     y_dis += int(dy)  # 输出
        #     y_dis = 500 if y_dis < 500 else y_dis
        #     y_dis = 2500 if y_dis > 2500 else y_dis
                                
        #     Board.setPWMServosPulse([20, 2, 3,int(y_dis), 6,int(x_dis)])
    
    return img

def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--Wheel', type=int, default=0, help='0 or 1')
    opt = parser.parse_args()
    return opt

#关闭前处理
def Stop(signum, frame):
    global __isRunning
    
    __isRunning = False
    print('关闭中...')
    MotorStop()  # 关闭所有电机

if __name__ == '__main__':
    opt = parse_opt()
    init()
    start()
    setWheel(**vars(opt))
    __isRunning = True
    __target_color = ('red')
    signal.signal(signal.SIGINT, Stop)
    cap = cv2.VideoCapture('http://127.0.0.1:8080?action=stream')
    while __isRunning:
        ret,img = cap.read()
        if ret:
            frame = img.copy()
            Frame = run(frame)  
            frame_resize = cv2.resize(Frame, (320, 240))
            cv2.imshow('frame', frame_resize)
            key = cv2.waitKey(1)
            if key == 27:
                break
        else:
            time.sleep(0.01)
    cv2.destroyAllWindows()

