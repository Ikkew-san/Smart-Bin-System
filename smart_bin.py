#!/usr/bin/python3
import RPi.GPIO as IO
import RPi_I2C_driver
import requests
import socket
import time

IO.setwarnings(False)
IO.setmode(IO.BCM)
lcd = RPi_I2C_driver.lcd()
API_URL = "http://192.168.43.11:8000/"

ledGreen = 27
ledYellow = 22
ledRed = 10
irSensor_01 = 18
irSensor_02 = 23
irSensor_03 = 24
irSensor_04 = 25

IO.setup(ledGreen, IO.OUT)
IO.setup(ledYellow, IO.OUT)
IO.setup(ledRed, IO.OUT)
IO.setup(irSensor_01, IO.IN)
IO.setup(irSensor_02, IO.IN)
IO.setup(irSensor_03, IO.IN)
IO.setup(irSensor_04, IO.IN)

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
ipaddr = s.getsockname()[0]
host = socket.gethostname()
r = requests.post(API_URL + "checkSmartbin", data={'hostname': host, 'ipaddress': ipaddr})
smartbin_id = r.json()['smartbin_id']
smartbin_status = r.json()['smartbin_status']
s.close()

def main():
    global smartbin_id, smartbin_status
    txtStatus = { "1": "Online", "2": "Full tank", "3": "Offline" }
    pos = { "1": 7, "2": 5, "3": 6}

    while True:
        r = requests.get(API_URL + "checkStatus/%s" %smartbin_id)
        if r.json()['smartbin_status'] != smartbin_status:
            lcd.lcd_clear()
            smartbin_status = r.json()["smartbin_status"]

        if smartbin_status == "1":
            IO.output(ledRed, IO.LOW)
            IO.output(ledYellow, IO.LOW)
            IO.output(ledGreen, IO.HIGH)
        elif smartbin_status == "2" or smartbin_status == "3":
            IO.output(ledGreen, IO.LOW)
            IO.output(ledYellow, IO.LOW)
            IO.output(ledRed, IO.HIGH)

        if r.json()["user_username"] is None or smartbin_status == "2" or smartbin_status == "3":
            lcd.lcd_display_string_pos("Smart Bin",1,5)
            lcd.lcd_display_string_pos(txtStatus[smartbin_status],2,pos[smartbin_status])
            lcd.lcd_display_string_pos("%s" %time.strftime("%m/%d/%Y"),3,5)
            lcd.lcd_display_string_pos("%s" %time.strftime("%H:%M:%S"),4,6)
                
            time.sleep(1)
        else:
            IO.output(ledRed, IO.LOW)
            IO.output(ledGreen, IO.LOW)
            IO.output(ledYellow, IO.HIGH)
            cumulative(r.json()["user_id"],r.json()["user_username"] )

def cumulative(user_id,user_username):
    global smartbin_id
    unit = 0
    state = 0
    cumulative_start = True
    
    lcd.lcd_clear()
    lcd.lcd_display_string_pos("Welcome",1,7)
    lcd.lcd_display_string(user_username,2)

    while cumulative_start :
        ir01 = IO.input(irSensor_01)
        ir02 = IO.input(irSensor_02)
        ir03 = IO.input(irSensor_03)
        ir04 = IO.input(irSensor_04)
        
        if state == 0:
            if (ir01 == 0 or ir03 == 0) and (ir02 == 1 and ir04 == 1):
                state = 1

            if (ir01 == 1 and ir03 == 1) and (ir02 == 0 or ir04 == 0):
                state = 2
                
        elif state == 1:
            if (ir01 == 1 and ir03 == 1) and (ir02 == 0 or ir04 == 0):
                state = 3

        elif state == 2:
            if (ir01 == 0 or ir03 == 0) and (ir02 == 1 and ir04 == 1):
                state = 4

        elif state == 3:
            if ir01 == 1 and ir02 == 1 and ir03 == 1 and ir04 == 1:
                unit = unit + 1
                r = requests.post(API_URL + "updatePoints", data={ 'id': smartbin_id })
                state = 0
            elif (ir01 == 0 or ir03 == 0) and (ir02 == 1 and ir04 == 1):
                state = 1

        elif state == 4:
            if ir01 == 1 and ir02 == 1 and ir03 == 1 and ir04 == 1:
                r = requests.post(API_URL + "logoutSmartbin", data={ 'id': smartbin_id })
                state = 0
            elif (ir01 == 1 and ir03 == 1) and (ir02 == 0 or ir04 == 0):
                state = 0                

        if ir01 == 1 and ir02 == 1 and ir03 == 1 and ir04 == 1:
            state = 0

        lcd.lcd_display_string("Unit: %d" %unit,4)

        r = requests.get(API_URL + "checkLogin/%s" %smartbin_id)
        if r.json()['user_id'] != user_id or r.json()['smartbin_status'] == "2":
            if r.json()['smartbin_status'] == "2":
                r = requests.post(API_URL + "logoutSmartbin", data={ 'id': smartbin_id })
                
            cumulative_start = False
            lcd.lcd_clear()
            
        time.sleep(0.02)

if __name__ == '__main__':   
    main()
