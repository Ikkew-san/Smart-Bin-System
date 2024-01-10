#!/usr/bin/python3
import RPi.GPIO as IO
import requests
import socket
import time

IO.setwarnings(False) 
IO.setmode(IO.BCM)
API_URL = "http://192.168.43.11:8000/"

TRIG = 4
ECHO = 17
 
IO.setup(TRIG, IO.OUT)
IO.setup(ECHO, IO.IN)

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
ipaddr = s.getsockname()[0]
host = socket.gethostname()
r = requests.post(API_URL + "checkSmartbin", data={'hostname': host, 'ipaddress': ipaddr})
smartbin_id = r.json()['smartbin_id']
smartbin_status = r.json()["smartbin_status"]
r = requests.post(API_URL + "checkAlertSmartbin", data = {'id': smartbin_id })
alert_id = None
if r.json()  == 0:
    alert_id = None
else:
    alert_id = r.json()
s.close()

while True:        
    if smartbin_status == "1":
        IO.output(TRIG, True)
        
        time.sleep(0.00001)
        IO.output(TRIG, False)
     
        StartTime = time.time()
        StopTime = time.time()
     
        while IO.input(ECHO) == 0:
            StartTime = time.time()
     
        while IO.input(ECHO) == 1:
            StopTime = time.time()
     
        TimeElapsed = StopTime - StartTime
        distance = (TimeElapsed * 34300) / 2

        if distance < 12:
            r = requests.post(API_URL + "alertSmartbin", data={'id': smartbin_id})
            smartbin_status = r.json()

        if alert_id is not None:
            if distance > 12:
                r = requests.post(API_URL + "setAlertSmartbin", data={'id': alert_id})
                alert_id = None
            
        time.sleep(0.1)
    else:
        r = requests.get(API_URL + "checkStatus/%s" %smartbin_id)
        smartbin_status = r.json()["smartbin_status"]
        
        if alert_id is None and smartbin_status == "2":
            r = requests.post(API_URL + "checkAlertSmartbin", data = {'id': smartbin_id })
            alert_id = r.json()
            
        time.sleep(1)

